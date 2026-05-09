"""Tests for registry.py — engagement table view."""

from __future__ import annotations

from rich.console import Console

from aletheia_control_plane.registry import (
    collect_entries,
    filter_entries,
    render_summary,
    render_table,
)
from aletheia_control_plane.schema import Phase
from tests.conftest import make_valid_record_dict, write_deployment


# --- collect_entries -------------------------------------------------


def test_collect_entries_empty(control_plane):
    entries = collect_entries(control_plane)
    assert entries == []


def test_collect_entries_one_engagement(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    entries = collect_entries(control_plane)
    assert len(entries) == 1
    assert entries[0].record is not None
    assert entries[0].record.engagement_code == "test_engagement_2026"
    assert entries[0].parse_error is None


def test_collect_entries_with_parse_error(control_plane):
    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=False)
    entries = collect_entries(control_plane)
    assert len(entries) == 1
    assert entries[0].record is None
    assert entries[0].parse_error is not None


def test_collect_entries_excludes_template(control_plane):
    # Even with no engagements created, template file should be excluded.
    entries = collect_entries(control_plane)
    assert entries == []


def test_collect_entries_multiple_engagements(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    write_deployment(
        control_plane,
        make_valid_record_dict(
            engagement_code="another_one",
            workspace_path="engagement_workspaces/another_one/",
            system_id="SYS-OTHER-001",
        ),
    )
    entries = collect_entries(control_plane)
    assert len(entries) == 2
    codes = {e.record.engagement_code for e in entries if e.record}
    assert codes == {"test_engagement_2026", "another_one"}


# --- filter_entries --------------------------------------------------


def test_filter_entries_no_filter_returns_all(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    entries = collect_entries(control_plane)
    filtered = filter_entries(entries)
    assert len(filtered) == 1


def test_filter_entries_phase_match(control_plane):
    write_deployment(control_plane, make_valid_record_dict(phase="active"))
    entries = collect_entries(control_plane)
    filtered = filter_entries(entries, include_phases={Phase.ACTIVE})
    assert len(filtered) == 1


def test_filter_entries_phase_no_match(control_plane):
    write_deployment(control_plane, make_valid_record_dict(phase="active"))
    entries = collect_entries(control_plane)
    filtered = filter_entries(entries, include_phases={Phase.CLOSED})
    assert len(filtered) == 0


def test_filter_entries_includes_parse_errors(control_plane):
    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=False)
    entries = collect_entries(control_plane)
    filtered = filter_entries(entries, include_phases={Phase.ACTIVE})
    # parse-error rows are always included regardless of phase filter
    assert len(filtered) == 1


# --- render_table ----------------------------------------------------


def test_render_table_returns_table(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    entries = collect_entries(control_plane)
    table = render_table(entries)
    assert table is not None
    assert table.row_count == 1


def test_render_table_with_console(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    entries = collect_entries(control_plane)
    console = Console(record=True, width=200)
    render_table(entries, console=console)
    output = console.export_text()
    assert "test_engagement_2026" in output
    assert "Test Client Inc." in output


def test_render_table_parse_error_row(control_plane):
    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=False)
    entries = collect_entries(control_plane)
    console = Console(record=True, width=200)
    render_table(entries, console=console)
    output = console.export_text()
    assert "test_engagement_2026" in output
    assert "parse error" in output


def test_render_table_no_interaction_renders_dash(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(last_interaction_date=None),
    )
    entries = collect_entries(control_plane)
    table = render_table(entries)
    assert table.row_count == 1


# --- render_summary --------------------------------------------------


def test_render_summary_empty():
    summary = render_summary([])
    assert summary["total"] == 0
    assert summary["parse_errors"] == 0
    for phase in Phase:
        assert summary[f"phase_{phase.value}"] == 0


def test_render_summary_counts(control_plane):
    write_deployment(control_plane, make_valid_record_dict(phase="active"))
    write_deployment(
        control_plane,
        make_valid_record_dict(
            engagement_code="onboarding_one",
            workspace_path="engagement_workspaces/onboarding_one/",
            system_id="SYS-ONBD-001",
            phase="onboarding",
        ),
    )
    entries = collect_entries(control_plane)
    summary = render_summary(entries)
    assert summary["total"] == 2
    assert summary["phase_active"] == 1
    assert summary["phase_onboarding"] == 1
    assert summary["parse_errors"] == 0


def test_render_summary_parse_errors_counted(control_plane):
    bad_data = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad_data, create_workspace=False)
    entries = collect_entries(control_plane)
    summary = render_summary(entries)
    assert summary["parse_errors"] == 1
    assert summary["total"] == 1
