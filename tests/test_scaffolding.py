"""Tests for scaffolding.py — new engagement creation."""

from __future__ import annotations

import pytest
import yaml

from aletheia_control_plane.scaffolding import (
    ScaffoldError,
    remove_engagement,
    scaffold_new_engagement,
)


# --- happy path -------------------------------------------------------


def test_scaffold_creates_deployment_file(control_plane):
    result = scaffold_new_engagement(control_plane, "new_engagement_2026")
    assert result.deployment_path.is_file()
    assert result.deployment_path.name == "new_engagement_2026.yaml"


def test_scaffold_creates_workspace_dir(control_plane):
    result = scaffold_new_engagement(control_plane, "new_engagement_2026")
    assert result.workspace_dir.is_dir()
    # workspace template's files should all be there
    expected_files = {
        "engagement_overview.md",
        "deployment_record.yaml",
        "quarterly_review_prep_template.md",
        "findings_status.md",
        "methodology_evolution_notes.md",
        "action_items.md",
        "communications_log.md",
    }
    actual_files = {p.name for p in result.workspace_dir.iterdir()}
    assert expected_files.issubset(actual_files)


def test_scaffold_substitutes_placeholders(control_plane):
    result = scaffold_new_engagement(control_plane, "abc_xyz_2026")
    # engagement_overview.md should have the code substituted
    overview = (result.workspace_dir / "engagement_overview.md").read_text()
    assert "abc_xyz_2026" in overview
    assert "[ENGAGEMENT CODE]" not in overview


def test_scaffold_seeds_engagement_code_in_deployment(control_plane):
    result = scaffold_new_engagement(control_plane, "abc_xyz_2026")
    data = yaml.safe_load(result.deployment_path.read_text())
    assert data["engagement_code"] == "abc_xyz_2026"
    assert data["workspace_path"] == "engagement_workspaces/abc_xyz_2026/"


def test_scaffold_workspace_mirror_matches_canonical(control_plane):
    result = scaffold_new_engagement(control_plane, "abc_xyz_2026")
    canonical = yaml.safe_load(result.deployment_path.read_text())
    mirror_path = result.workspace_dir / "deployment_record.yaml"
    mirror = yaml.safe_load(mirror_path.read_text())
    assert canonical == mirror


def test_scaffold_returns_files_created(control_plane):
    result = scaffold_new_engagement(control_plane, "new_engagement_2026")
    assert result.deployment_path in result.files_created
    # workspace files (including the mirror) should be there
    assert any(
        f.name == "engagement_overview.md" for f in result.files_created
    )


# --- error cases ------------------------------------------------------


def test_scaffold_invalid_code_format(control_plane):
    with pytest.raises(ScaffoldError, match="not valid"):
        scaffold_new_engagement(control_plane, "Bad-Code")


def test_scaffold_too_short_code(control_plane):
    with pytest.raises(ScaffoldError, match="too short"):
        scaffold_new_engagement(control_plane, "ab")


def test_scaffold_too_long_code(control_plane):
    with pytest.raises(ScaffoldError, match="too long"):
        scaffold_new_engagement(control_plane, "a" + "b" * 100)


def test_scaffold_collision_deployment_exists(control_plane):
    scaffold_new_engagement(control_plane, "new_engagement_2026")
    with pytest.raises(ScaffoldError, match="deployment record already exists"):
        scaffold_new_engagement(control_plane, "new_engagement_2026")


def test_scaffold_collision_workspace_exists(control_plane):
    scaffold_new_engagement(control_plane, "new_engagement_2026")
    # remove only the deployment file, leaving the workspace
    (control_plane.deployments_dir / "new_engagement_2026.yaml").unlink()
    with pytest.raises(ScaffoldError, match="workspace directory already exists"):
        scaffold_new_engagement(control_plane, "new_engagement_2026")


def test_scaffold_missing_deployment_template(tmp_path, control_plane):
    control_plane.deployment_template_path.unlink()
    with pytest.raises(ScaffoldError, match="deployment template not found"):
        scaffold_new_engagement(control_plane, "new_engagement_2026")


def test_scaffold_missing_workspace_template(control_plane):
    import shutil
    shutil.rmtree(control_plane.workspace_template_dir)
    with pytest.raises(ScaffoldError, match="workspace template not found"):
        scaffold_new_engagement(control_plane, "new_engagement_2026")


# --- remove_engagement -------------------------------------------------


def test_remove_engagement_removes_both(control_plane):
    scaffold_new_engagement(control_plane, "to_remove_2026")
    deployment_path, workspace_dir = remove_engagement(control_plane, "to_remove_2026")
    assert not deployment_path.exists()
    assert not workspace_dir.exists()


def test_remove_engagement_partial(control_plane):
    scaffold_new_engagement(control_plane, "to_remove_2026")
    # remove only the deployment file
    (control_plane.deployments_dir / "to_remove_2026.yaml").unlink()
    deployment_path, workspace_dir = remove_engagement(control_plane, "to_remove_2026")
    assert not workspace_dir.exists()


def test_remove_engagement_missing_raises(control_plane):
    with pytest.raises(FileNotFoundError):
        remove_engagement(control_plane, "never_existed")


def test_remove_engagement_only_deployment_present(control_plane):
    """Cover the branch where workspace dir doesn't exist but deployment does."""

    scaffold_new_engagement(control_plane, "to_remove_2026")
    # remove only the workspace dir
    import shutil
    shutil.rmtree(control_plane.workspaces_dir / "to_remove_2026")
    deployment_path, workspace_dir = remove_engagement(
        control_plane, "to_remove_2026"
    )
    assert not deployment_path.exists()


def test_scaffold_handles_template_subdirs(control_plane):
    """Cover the directory-skip branch in workspace template traversal."""

    subdir = control_plane.workspace_template_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested_file.md").write_text("nested content for [ENGAGEMENT CODE]\n")
    result = scaffold_new_engagement(control_plane, "with_subdir_2026")
    nested = result.workspace_dir / "subdir" / "nested_file.md"
    assert nested.is_file()
    assert "with_subdir_2026" in nested.read_text()


def test_scaffold_when_template_has_no_deployment_mirror(control_plane):
    """Cover the branch where workspace mirror gets appended separately."""

    (control_plane.workspace_template_dir / "deployment_record.yaml").unlink()
    result = scaffold_new_engagement(control_plane, "no_mirror_template_2026")
    # mirror should still exist (seeded from deployment template)
    mirror = result.workspace_dir / "deployment_record.yaml"
    assert mirror.is_file()
    # and it should be in files_created
    assert mirror in result.files_created


# --- post-scaffold validation -----------------------------------------


def test_scaffolded_engagement_validates_after_filling(control_plane):
    """A scaffolded engagement, once required fields are filled, should validate cleanly."""

    from aletheia_control_plane.validate import validate_engagement
    from tests.conftest import make_valid_record_dict

    result = scaffold_new_engagement(control_plane, "fill_me_2026")
    # Overwrite with a valid record (in production, the operator does this by hand).
    record = make_valid_record_dict(
        engagement_code="fill_me_2026",
        workspace_path="engagement_workspaces/fill_me_2026/",
    )
    serializable = {
        k: (v.isoformat() if hasattr(v, "isoformat") else v)
        for k, v in record.items()
    }
    result.deployment_path.write_text(
        yaml.safe_dump(serializable, sort_keys=False), encoding="utf-8"
    )
    # Mirror must match.
    (result.workspace_dir / "deployment_record.yaml").write_text(
        yaml.safe_dump(serializable, sort_keys=False), encoding="utf-8"
    )
    report = validate_engagement(control_plane, "fill_me_2026")
    assert report.ok is True, "\n".join(i.render() for i in report.issues)
