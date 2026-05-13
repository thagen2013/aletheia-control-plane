"""Tests for validate.py — cross-reference validator."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aletheia_control_plane.validate import (
    Issue,
    Severity,
    ValidationReport,
    discover_deployments,
    discover_engagement_workspaces,
    load_deployment,
    load_yaml,
    parse_methodology_versions,
    parse_overlay_ids,
    validate_engagement,
    validate_root,
    validate_workspace_mirror,
)
from tests.conftest import make_valid_record_dict, write_deployment


# --- ValidationReport / Issue ------------------------------------------


def test_validation_report_starts_empty():
    report = ValidationReport()
    assert report.ok is True
    assert report.errors == []
    assert report.warnings == []


def test_validation_report_add_error():
    report = ValidationReport()
    report.add(Severity.ERROR, "boom")
    assert report.ok is False
    assert len(report.errors) == 1
    assert len(report.warnings) == 0


def test_validation_report_add_warning():
    report = ValidationReport()
    report.add(Severity.WARNING, "huh")
    assert report.ok is True
    assert len(report.warnings) == 1


def test_validation_report_merge():
    a = ValidationReport()
    a.add(Severity.ERROR, "a-err")
    b = ValidationReport()
    b.add(Severity.WARNING, "b-warn")
    a.merge(b)
    assert len(a.issues) == 2


def test_issue_render_includes_components():
    issue = Issue(
        severity=Severity.ERROR,
        message="something broke",
        file_path=Path("/tmp/x.yaml"),
        field_path="some.field",
    )
    rendered = issue.render()
    assert "[error]" in rendered
    assert "x.yaml" in rendered
    assert "(some.field)" in rendered
    assert "something broke" in rendered


def test_issue_render_minimal():
    issue = Issue(severity=Severity.WARNING, message="just a warning")
    rendered = issue.render()
    assert "[warning]" in rendered
    assert "just a warning" in rendered


# --- load_yaml --------------------------------------------------------


def test_load_yaml_valid_file(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("a: 1\nb: 2\n")
    assert load_yaml(p) == {"a": 1, "b": 2}


def test_load_yaml_empty_file_returns_none(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("")
    assert load_yaml(p) is None


def test_load_yaml_non_mapping_raises(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("- 1\n- 2\n")
    with pytest.raises(ValueError, match="not a mapping"):
        load_yaml(p)


# --- parsers ----------------------------------------------------------


def test_parse_methodology_versions(control_plane):
    """The fixture mirrors the real changelog: only the current shipped
    version gets a dedicated heading; earlier versions live in a prose
    ``## Earlier versions`` section and are not parsed out individually."""

    versions = parse_methodology_versions(control_plane.changelog_path)
    assert versions == {"0.5.0"}


def test_parse_methodology_versions_missing_file(tmp_path):
    versions = parse_methodology_versions(tmp_path / "nonexistent.md")
    assert versions == set()


def test_parse_methodology_versions_handles_v_prefix(tmp_path):
    p = tmp_path / "changelog.md"
    p.write_text("## v1.2.3 — release\n## 0.4.0 — earlier\n")
    versions = parse_methodology_versions(p)
    assert "1.2.3" in versions
    assert "0.4.0" in versions


def test_parse_overlay_ids(control_plane_with_overlay):
    overlay_ids = parse_overlay_ids(
        control_plane_with_overlay.overlay_registry_path
    )
    assert "overlay-001-test-overlay" in overlay_ids


def test_parse_overlay_ids_empty_registry(control_plane):
    overlay_ids = parse_overlay_ids(control_plane.overlay_registry_path)
    assert overlay_ids == set()


def test_parse_overlay_ids_missing_file(tmp_path):
    assert parse_overlay_ids(tmp_path / "nonexistent.md") == set()


# --- discover ---------------------------------------------------------


def test_discover_deployments_excludes_template(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    paths = discover_deployments(control_plane)
    assert len(paths) == 1
    assert paths[0].name == "test_engagement_2026.yaml"


def test_discover_engagement_workspaces_excludes_template(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    workspaces = discover_engagement_workspaces(control_plane)
    assert len(workspaces) == 1
    assert workspaces[0].name == "test_engagement_2026"


def test_discover_returns_empty_for_clean_root(control_plane):
    assert discover_deployments(control_plane) == []
    assert discover_engagement_workspaces(control_plane) == []


# --- load_deployment --------------------------------------------------


def test_load_deployment_valid(control_plane):
    path = write_deployment(control_plane, make_valid_record_dict())
    record, report = load_deployment(path)
    assert record is not None
    assert record.engagement_code == "test_engagement_2026"
    assert report.ok is True


def test_load_deployment_invalid_yaml(control_plane):
    path = control_plane.deployments_dir / "broken.yaml"
    path.write_text("a: [unclosed\n")
    record, report = load_deployment(path)
    assert record is None
    assert any("YAML parse error" in i.message for i in report.errors)


def test_load_deployment_non_mapping(control_plane):
    path = control_plane.deployments_dir / "nonmap.yaml"
    path.write_text("- just\n- a\n- list\n")
    record, report = load_deployment(path)
    assert record is None
    assert any("not a mapping" in i.message for i in report.errors)


def test_load_deployment_empty(control_plane):
    path = control_plane.deployments_dir / "empty.yaml"
    path.write_text("")
    record, report = load_deployment(path)
    assert record is None
    assert any("empty" in i.message for i in report.errors)


def test_load_deployment_template_placeholder(control_plane):
    path = control_plane.deployments_dir / "tmpl.yaml"
    template_data = make_valid_record_dict(
        engagement_code="<engagement_code>",
        workspace_path="engagement_workspaces/<engagement_code>/",
    )
    write_deployment(control_plane, template_data, create_workspace=False)
    template_path = control_plane.deployments_dir / "<engagement_code>.yaml"
    record, report = load_deployment(template_path)
    assert record is None
    assert any("template" in i.message.lower() for i in report.errors)


def test_load_deployment_invalid_record(control_plane):
    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=False)
    path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    record, report = load_deployment(path)
    assert record is None
    assert any("system_id" in (i.field_path or "") for i in report.errors)


# --- workspace mirror -------------------------------------------------


def test_workspace_mirror_matches(control_plane):
    write_deployment(control_plane, make_valid_record_dict(), mirror_matches=True)
    deployment_path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    report = validate_workspace_mirror(deployment_path, workspace_dir)
    assert report.ok is True


def test_workspace_mirror_drift_detected(control_plane):
    write_deployment(control_plane, make_valid_record_dict(), mirror_matches=False)
    deployment_path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    report = validate_workspace_mirror(deployment_path, workspace_dir)
    assert report.ok is False
    assert any("client_legal_name" in (i.field_path or "") for i in report.errors)


def test_workspace_mirror_missing(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(),
        create_workspace=True,
    )
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    # delete the mirror
    (workspace_dir / "deployment_record.yaml").unlink()
    deployment_path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    report = validate_workspace_mirror(deployment_path, workspace_dir)
    assert any("workspace mirror missing" in i.message for i in report.errors)


def test_workspace_mirror_yaml_error(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    (workspace_dir / "deployment_record.yaml").write_text("a: [unclosed\n")
    deployment_path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    report = validate_workspace_mirror(deployment_path, workspace_dir)
    assert any("YAML parse error" in i.message for i in report.errors)


def test_workspace_mirror_empty_file(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    (workspace_dir / "deployment_record.yaml").write_text("")
    deployment_path = control_plane.deployments_dir / "test_engagement_2026.yaml"
    report = validate_workspace_mirror(deployment_path, workspace_dir)
    assert any("empty" in i.message for i in report.errors)


# --- validate_root: happy path ----------------------------------------


def test_validate_root_clean(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    report = validate_root(control_plane)
    assert report.ok is True


def test_validate_root_no_engagements_clean(control_plane):
    report = validate_root(control_plane)
    assert report.ok is True


# --- validate_root: methodology version drift -------------------------


def test_validate_root_unknown_methodology_version_flagged(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(methodology_version="9.9.9"),
    )
    report = validate_root(control_plane)
    assert any(
        "methodology_version" in (i.field_path or "") for i in report.errors
    )


def test_validate_root_warns_when_changelog_empty(control_plane):
    control_plane.changelog_path.write_text("# Empty\n")
    write_deployment(
        control_plane,
        make_valid_record_dict(methodology_version="9.9.9"),
    )
    report = validate_root(control_plane)
    assert any(
        "no methodology versions parsed" in i.message for i in report.warnings
    )
    # Contract: when the changelog has no parseable versions, every
    # methodology_version is permitted (cannot validate against an
    # absent source of truth). Lock this in so a future regression
    # that quietly rejects all versions on empty changelog is caught.
    assert not any(
        "methodology_version" in (i.field_path or "") for i in report.errors
    )
    assert report.ok is True


# --- validate_root: overlay -------------------------------------------


def test_validate_root_known_overlay_ok(control_plane_with_overlay):
    write_deployment(
        control_plane_with_overlay,
        make_valid_record_dict(overlay_id="overlay-001-test-overlay"),
    )
    report = validate_root(control_plane_with_overlay)
    assert report.ok is True


def test_validate_root_unknown_overlay_flagged(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(overlay_id="overlay-999-fake"),
    )
    report = validate_root(control_plane)
    assert any(
        "overlay_id" in (i.field_path or "") for i in report.errors
    )


# --- validate_root: filename / engagement_code -----------------------


def test_validate_root_filename_mismatch(control_plane):
    record_dict = make_valid_record_dict()
    write_deployment(control_plane, record_dict)
    # Rename the file so it no longer matches engagement_code.
    canonical = control_plane.deployments_dir / "test_engagement_2026.yaml"
    renamed = control_plane.deployments_dir / "different_name.yaml"
    canonical.rename(renamed)
    report = validate_root(control_plane)
    assert any(
        "filename" in i.message and "engagement_code" in i.message
        for i in report.errors
    )


def test_validate_root_duplicate_engagement_code(control_plane):
    record_dict = make_valid_record_dict()
    write_deployment(control_plane, record_dict)
    # Create a second YAML with the same engagement_code under a different filename.
    dup = control_plane.deployments_dir / "duplicate.yaml"
    dup.write_text(
        yaml.safe_dump(
            {
                **record_dict,
                "deployment_date": "2026-01-15",
                "last_self_test_verified": "2026-01-16",
                "last_interaction_date": "2026-01-20",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = validate_root(control_plane)
    assert any(
        "also defined" in i.message for i in report.errors
    )


# --- validate_root: workspace presence -------------------------------


def test_validate_root_workspace_missing_for_deployment(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(),
        create_workspace=False,
    )
    report = validate_root(control_plane)
    assert any(
        "engagement workspace directory not found" in i.message
        for i in report.errors
    )


def test_validate_root_orphaned_workspace_flagged(control_plane):
    # Create a workspace dir with no deployment file.
    orphan_dir = control_plane.workspaces_dir / "orphan_engagement"
    orphan_dir.mkdir()
    report = validate_root(control_plane)
    assert any(
        "no corresponding deployment record" in i.message for i in report.errors
    )


def test_validate_root_workspace_with_failed_deployment_not_double_reported(
    control_plane,
):
    """If deployment file exists but fails to parse, workspace shouldn't ALSO be flagged.

    This specifically tests the bug where a parse failure caused the
    workspace to be reported as 'orphaned' on top of the parse error.
    """

    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=True)
    report = validate_root(control_plane)
    assert not any(
        "no corresponding deployment record" in i.message for i in report.errors
    )


# --- validate_engagement ----------------------------------------------


def test_validate_engagement_clean(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    report = validate_engagement(control_plane, "test_engagement_2026")
    assert report.ok is True


def test_validate_engagement_missing_deployment(control_plane):
    report = validate_engagement(control_plane, "nonexistent_engagement")
    assert any(
        "deployment file not found" in i.message for i in report.errors
    )


def test_validate_engagement_unknown_methodology(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(methodology_version="9.9.9"),
    )
    report = validate_engagement(control_plane, "test_engagement_2026")
    assert any(
        "methodology_version" in (i.field_path or "") for i in report.errors
    )


def test_validate_engagement_unknown_overlay(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(overlay_id="overlay-999-fake"),
    )
    report = validate_engagement(control_plane, "test_engagement_2026")
    assert any(
        "overlay_id" in (i.field_path or "") for i in report.errors
    )


def test_validate_engagement_known_overlay_ok(control_plane_with_overlay):
    write_deployment(
        control_plane_with_overlay,
        make_valid_record_dict(overlay_id="overlay-001-test-overlay"),
    )
    report = validate_engagement(control_plane_with_overlay, "test_engagement_2026")
    assert report.ok is True


def test_validate_engagement_workspace_missing(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(),
        create_workspace=False,
    )
    report = validate_engagement(control_plane, "test_engagement_2026")
    assert any(
        "workspace directory not found" in i.message for i in report.errors
    )


def test_validate_engagement_mirror_drift(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(),
        mirror_matches=False,
    )
    report = validate_engagement(control_plane, "test_engagement_2026")
    assert any("differs from canonical" in i.message for i in report.errors)


def test_validate_engagement_unparseable_record_short_circuits(control_plane):
    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=True)
    report = validate_engagement(control_plane, "test_engagement_2026")
    # Should report the parse error and stop before workspace checks.
    assert any("system_id" in (i.field_path or "") for i in report.errors)
    # Lock in the short-circuit: if the schema parse fails, the
    # workspace mirror / structure checks must NOT run, otherwise a
    # cascade of follow-on errors hides the root cause. If the early
    # return in validate_engagement is removed, this assertion fails.
    assert not any(
        "workspace" in i.message.lower() for i in report.issues
    )
