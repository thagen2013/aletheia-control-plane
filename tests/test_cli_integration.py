"""End-to-end CLI tests using click's CliRunner.

These tests exercise the click entry point with --root pointing at a
fixture control plane root, verifying both happy paths and error
exits.
"""

from __future__ import annotations

from click.testing import CliRunner

from aletheia_control_plane.cli import cli
from tests.conftest import make_valid_record_dict, write_deployment


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Operator CLI" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_cli_validate_clean(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(cli, ["--root", str(control_plane.root), "validate"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_cli_validate_with_errors(control_plane):
    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=False)
    runner = CliRunner()
    result = runner.invoke(cli, ["--root", str(control_plane.root), "validate"])
    assert result.exit_code == 1
    assert "error" in result.output.lower()


def test_cli_validate_specific_engagement(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root", str(control_plane.root), "validate", "test_engagement_2026"],
    )
    assert result.exit_code == 0


def test_cli_validate_missing_engagement(control_plane):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "validate", "never_existed"]
    )
    assert result.exit_code == 1
    assert "deployment file not found" in result.output


def test_cli_validate_warning_only(control_plane):
    """A warning without errors should exit 0 but still print warning text."""

    control_plane.versions_manifest_path.unlink()
    runner = CliRunner()
    result = runner.invoke(cli, ["--root", str(control_plane.root), "validate"])
    assert result.exit_code == 0
    assert "warning" in result.output.lower()


def test_cli_new_engagement(control_plane):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "new", "fresh_engagement_2026"]
    )
    assert result.exit_code == 0
    assert "scaffolded" in result.output
    assert (
        control_plane.deployments_dir / "fresh_engagement_2026.yaml"
    ).is_file()


def test_cli_new_engagement_invalid_code(control_plane):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "new", "Bad-Code"]
    )
    assert result.exit_code == 1
    assert "not valid" in result.output


def test_cli_new_engagement_collision(control_plane):
    runner = CliRunner()
    runner.invoke(
        cli, ["--root", str(control_plane.root), "new", "first_2026"]
    )
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "new", "first_2026"]
    )
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_cli_registry_empty(control_plane):
    runner = CliRunner()
    result = runner.invoke(cli, ["--root", str(control_plane.root), "registry"])
    assert result.exit_code == 0
    assert "no engagements found" in result.output


def test_cli_registry_with_engagement(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root", str(control_plane.root), "registry"],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "test_engagement_2026" in result.output


def test_cli_registry_phase_filter(control_plane):
    write_deployment(control_plane, make_valid_record_dict(phase="active"))
    write_deployment(
        control_plane,
        make_valid_record_dict(
            engagement_code="closed_one",
            workspace_path="engagement_workspaces/closed_one/",
            system_id="SYS-CLOSED-001",
            phase="closed",
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--root",
            str(control_plane.root),
            "registry",
            "--phase",
            "active",
        ],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "test_engagement_2026" in result.output
    assert "closed_one" not in result.output


def test_cli_methodology_status_empty(control_plane):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "methodology-status"]
    )
    assert result.exit_code == 0
    assert "no engagements found" in result.output


def test_cli_methodology_status_current(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root", str(control_plane.root), "methodology-status"],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "test_engagement_2026" in result.output


def test_cli_methodology_status_warns_on_missing_manifest(control_plane):
    """If the versions manifest is missing, the command must warn so the
    operator knows the source of truth is gone."""

    control_plane.versions_manifest_path.unlink()
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--root", str(control_plane.root), "methodology-status"]
    )
    assert "no methodology versions" in result.output


def test_cli_methodology_status_lists_stale(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.4.0"))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root", str(control_plane.root), "methodology-status"],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "behind" in result.output
    assert "test_engagement_2026" in result.output


def test_cli_methodology_status_surfaces_parse_errors(control_plane):
    """When all deployments fail to parse, the command must NOT print the
    same 'no engagements found' it prints for a truly empty fleet."""

    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=False)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--root", str(control_plane.root), "methodology-status"],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "no engagements found" not in result.output
    assert "1 malformed deployment" in result.output


def test_cli_prep_review(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--root",
            str(control_plane.root),
            "prep-review",
            "test_engagement_2026",
            "--year",
            "2026",
            "--quarter",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "scaffolded" in result.output
    assert (
        control_plane.workspaces_dir
        / "test_engagement_2026"
        / "quarterly_review_2026Q1.md"
    ).is_file()


def test_cli_prep_review_missing_engagement(control_plane):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--root",
            str(control_plane.root),
            "prep-review",
            "never_existed",
        ],
    )
    assert result.exit_code == 1
    assert "deployment record not found" in result.output


def test_cli_prep_review_overwrite(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    runner = CliRunner()
    args = [
        "--root",
        str(control_plane.root),
        "prep-review",
        "test_engagement_2026",
        "--year",
        "2026",
        "--quarter",
        "1",
    ]
    runner.invoke(cli, args)
    # Second invocation should fail without --overwrite
    second = runner.invoke(cli, args)
    assert second.exit_code == 1
    # With --overwrite it should succeed
    third = runner.invoke(cli, args + ["--overwrite"])
    assert third.exit_code == 0


def test_cli_invalid_root(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["--root", str(tmp_path), "validate"])
    assert result.exit_code == 2
    assert "does not look like a control plane root" in result.output


def test_cli_no_root_no_cwd(tmp_path, monkeypatch):
    """When neither --root nor cwd resolves, exit cleanly."""

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["validate"])
    assert result.exit_code == 2
    assert "No control plane root" in result.output
