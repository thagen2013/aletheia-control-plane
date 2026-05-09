"""Tests for review_prep.py."""

from __future__ import annotations

from datetime import date

import pytest

from aletheia_control_plane.review_prep import (
    ReviewPrepError,
    determine_quarter,
    scaffold_review_prep,
)
from tests.conftest import make_valid_record_dict, write_deployment


# --- determine_quarter ------------------------------------------------


@pytest.mark.parametrize(
    "ref_date,expected",
    [
        (date(2026, 1, 15), (2026, 1)),
        (date(2026, 3, 31), (2026, 1)),
        (date(2026, 4, 1), (2026, 2)),
        (date(2026, 6, 30), (2026, 2)),
        (date(2026, 7, 1), (2026, 3)),
        (date(2026, 9, 30), (2026, 3)),
        (date(2026, 10, 1), (2026, 4)),
        (date(2026, 12, 31), (2026, 4)),
    ],
)
def test_determine_quarter(ref_date, expected):
    assert determine_quarter(ref_date) == expected


def test_determine_quarter_default_uses_today():
    # Just verify it returns sensible values
    year, quarter = determine_quarter()
    assert 2024 <= year <= 2030  # generous range
    assert 1 <= quarter <= 4


# --- scaffold_review_prep happy path ---------------------------------


def test_scaffold_review_prep_creates_file(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    result = scaffold_review_prep(
        control_plane, "test_engagement_2026", year=2026, quarter=1
    )
    assert result.output_path.is_file()
    assert result.output_path.name == "quarterly_review_2026Q1.md"
    assert result.review_year == 2026
    assert result.review_quarter == 1


def test_scaffold_review_prep_substitutes_metadata(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    result = scaffold_review_prep(
        control_plane, "test_engagement_2026", year=2026, quarter=2
    )
    text = result.output_path.read_text()
    assert "test_engagement_2026 2026Q2" in text
    assert "[ENGAGEMENT CODE]" not in text
    assert "0.5.0" in text


def test_scaffold_review_prep_uses_current_quarter_by_default(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    result = scaffold_review_prep(control_plane, "test_engagement_2026")
    expected_year, expected_quarter = determine_quarter()
    assert result.review_year == expected_year
    assert result.review_quarter == expected_quarter


def test_scaffold_review_prep_partial_kwargs(control_plane):
    """If only one of year/quarter is provided, the other comes from today."""

    write_deployment(control_plane, make_valid_record_dict())
    result = scaffold_review_prep(
        control_plane, "test_engagement_2026", year=2027
    )
    assert result.review_year == 2027
    today_quarter = determine_quarter()[1]
    assert result.review_quarter == today_quarter


# --- error cases -----------------------------------------------------


def test_scaffold_review_prep_missing_engagement(control_plane):
    with pytest.raises(ReviewPrepError, match="deployment record not found"):
        scaffold_review_prep(control_plane, "never_existed", year=2026, quarter=1)


def test_scaffold_review_prep_unparseable_record(control_plane):
    bad = make_valid_record_dict(system_id="invalid")
    write_deployment(control_plane, bad, create_workspace=True)
    with pytest.raises(ReviewPrepError, match="did not parse"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=1
        )


def test_scaffold_review_prep_missing_workspace(control_plane):
    write_deployment(
        control_plane, make_valid_record_dict(), create_workspace=False
    )
    with pytest.raises(ReviewPrepError, match="workspace directory not found"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=1
        )


def test_scaffold_review_prep_missing_template(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    workspace_dir = control_plane.workspaces_dir / "test_engagement_2026"
    (workspace_dir / "quarterly_review_prep_template.md").unlink()
    with pytest.raises(ReviewPrepError, match="template not found"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=1
        )


def test_scaffold_review_prep_invalid_quarter(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    with pytest.raises(ReviewPrepError, match="quarter must be"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=5
        )
    with pytest.raises(ReviewPrepError, match="quarter must be"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=0
        )


def test_scaffold_review_prep_existing_file_no_overwrite(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    scaffold_review_prep(
        control_plane, "test_engagement_2026", year=2026, quarter=1
    )
    with pytest.raises(ReviewPrepError, match="already exists"):
        scaffold_review_prep(
            control_plane, "test_engagement_2026", year=2026, quarter=1
        )


def test_scaffold_review_prep_overwrite_succeeds(control_plane):
    write_deployment(control_plane, make_valid_record_dict())
    scaffold_review_prep(
        control_plane, "test_engagement_2026", year=2026, quarter=1
    )
    result = scaffold_review_prep(
        control_plane,
        "test_engagement_2026",
        year=2026,
        quarter=1,
        overwrite=True,
    )
    assert result.output_path.is_file()
