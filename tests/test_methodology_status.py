"""Tests for methodology_status.py."""

from __future__ import annotations

from textwrap import dedent

import pytest
from rich.console import Console

from aletheia_control_plane.methodology_status import (
    compute_status,
    determine_current_version,
    find_stale_engagements,
    render_status_table,
)
from aletheia_control_plane.schema import Phase
from tests.conftest import make_valid_record_dict, write_deployment


_REAL_SHAPE_CHANGELOG = dedent(
    """
    # Methodology Changelog

    ## v0.5.0 (current shipped) — Test fixture for real shape

    Test methodology release.

    ## Earlier versions

    Earlier versions (v0.1.2 through v0.4.0) shipped during the
    methodology-development phase before the first engagement-ready
    release.
    """
).lstrip()


# --- determine_current_version ---------------------------------------


def test_determine_current_version_picks_max():
    versions = {"0.1.0", "0.5.0", "0.4.0"}
    assert determine_current_version(versions) == "0.5.0"


def test_determine_current_version_handles_empty_set():
    assert determine_current_version(set()) is None


def test_determine_current_version_invalid_semver_raises():
    versions = {"not-a-version"}
    with pytest.raises(ValueError, match="not a semver"):
        determine_current_version(versions)


def test_determine_current_version_with_v_prefix():
    versions = {"0.5.0", "v0.6.0"}
    # both should be in the set as-is; max is by parsed tuple
    result = determine_current_version(versions)
    # Either v0.6.0 or 0.6.0 string is fine; tuple ordering says 0.6.0 wins
    assert result.removeprefix("v") == "0.6.0"


def test_determine_current_version_with_prerelease_treated_as_base():
    versions = {"0.5.0", "0.5.0-rc1"}
    # treated equal at base; max returns whichever comes first by python tie-break
    result = determine_current_version(versions)
    assert result.startswith("0.5.0")


# --- compute_status: empty -------------------------------------------


def test_compute_status_no_engagements(control_plane):
    entries, current, known, parse_errors = compute_status(control_plane)
    assert entries == []
    assert current == "0.5.0"
    assert known == {"0.5.0"}
    assert parse_errors == []


# --- compute_status: with engagements --------------------------------


def test_compute_status_current(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.5.0"))
    entries, current, _, _ = compute_status(control_plane)
    assert len(entries) == 1
    assert entries[0].is_current is True
    assert entries[0].is_unknown is False
    assert current == "0.5.0"


def test_compute_status_behind(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.4.0"))
    entries, current, _, _ = compute_status(control_plane)
    assert entries[0].is_current is False
    assert entries[0].is_unknown is False


def test_compute_status_unknown_version(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="9.9.9"))
    entries, _, _, _ = compute_status(control_plane)
    assert entries[0].is_unknown is True


def test_compute_status_skips_parse_errors(control_plane):
    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=False)
    result = compute_status(control_plane)
    entries = result[0]
    assert entries == []


def test_compute_status_returns_parse_errors(control_plane):
    """Malformed deployments must be reported, not silently dropped."""

    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=False)
    *_, parse_errors = compute_status(control_plane)
    assert len(parse_errors) == 1


def test_compute_status_behind_with_real_shape_changelog(control_plane):
    """A 0.4.0 deployment must be classified 'behind', not 'unknown',
    against a changelog whose earlier versions live in a prose section
    (matching the real repo's changelog.md layout).
    """

    control_plane.changelog_path.write_text(
        _REAL_SHAPE_CHANGELOG, encoding="utf-8"
    )
    write_deployment(
        control_plane, make_valid_record_dict(methodology_version="0.4.0")
    )
    entries, current, _, _ = compute_status(control_plane)
    assert current == "0.5.0"
    assert len(entries) == 1
    assert entries[0].is_unknown is False
    assert entries[0].is_current is False


def test_compute_status_ahead_of_current_is_unknown(control_plane):
    """A deployment ahead of the current shipped version is suspect
    (likely typo or unreleased) and stays 'unknown'."""

    control_plane.changelog_path.write_text(
        _REAL_SHAPE_CHANGELOG, encoding="utf-8"
    )
    write_deployment(
        control_plane, make_valid_record_dict(methodology_version="9.9.9")
    )
    entries, _, _, _ = compute_status(control_plane)
    assert entries[0].is_unknown is True


def test_compute_status_v_prefix_normalized(control_plane):
    write_deployment(
        control_plane, make_valid_record_dict(methodology_version="v0.5.0")
    )
    entries, _, _, _ = compute_status(control_plane)
    assert entries[0].is_current is True


# --- find_stale_engagements ------------------------------------------


def test_find_stale_returns_behind_engagements(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.4.0"))
    entries, _, _, _ = compute_status(control_plane)
    stale = find_stale_engagements(entries)
    assert len(stale) == 1


def test_find_stale_excludes_current(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.5.0"))
    entries, _, _, _ = compute_status(control_plane)
    assert find_stale_engagements(entries) == []


def test_find_stale_excludes_unknown_version(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="9.9.9"))
    entries, _, _, _ = compute_status(control_plane)
    # Unknown versions are surfaced separately, not as 'stale'
    assert find_stale_engagements(entries) == []


def test_find_stale_excludes_closed(control_plane):
    write_deployment(
        control_plane,
        make_valid_record_dict(methodology_version="0.4.0", phase="closed"),
    )
    entries, _, _, _ = compute_status(control_plane)
    assert find_stale_engagements(entries) == []


# --- render_status_table ---------------------------------------------


def test_render_status_table_no_entries():
    table = render_status_table([], current_version=None)
    assert table.row_count == 0


def test_render_status_table_with_console(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.5.0"))
    entries, current, _, _ = compute_status(control_plane)
    console = Console(record=True, width=200)
    render_status_table(entries, current, console=console)
    output = console.export_text()
    assert "test_engagement_2026" in output
    assert "current" in output


def test_render_status_table_unknown_version(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="9.9.9"))
    entries, current, _, _ = compute_status(control_plane)
    console = Console(record=True, width=200)
    render_status_table(entries, current, console=console)
    output = console.export_text()
    assert "unknown version" in output


def test_render_status_table_behind(control_plane):
    write_deployment(control_plane, make_valid_record_dict(methodology_version="0.4.0"))
    entries, current, _, _ = compute_status(control_plane)
    console = Console(record=True, width=200)
    render_status_table(entries, current, console=console)
    output = console.export_text()
    assert "behind" in output
