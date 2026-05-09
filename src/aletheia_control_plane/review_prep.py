"""Scaffold a quarterly review prep file for an engagement.

Copies ``quarterly_review_prep_template.md`` from the engagement
workspace into ``quarterly_review_<YYYY>Q<#>.md`` in the same
workspace, with known fields auto-filled from the deployment record.

The auto-fill is conservative: it substitutes only fields that can be
mechanically derived (engagement code, methodology version, hetarios
version, review-session-quarter labeling). The operator fills the
substantive content (action item statuses, finding status changes,
talking points).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from aletheia_control_plane.paths import ControlPlaneRoot
from aletheia_control_plane.schema import DeploymentRecord
from aletheia_control_plane.validate import load_deployment


class ReviewPrepError(RuntimeError):
    """Raised when review prep scaffolding cannot proceed."""


@dataclass
class ReviewPrepResult:
    """Result of a review-prep scaffolding."""

    engagement_code: str
    review_year: int
    review_quarter: int
    output_path: Path


def determine_quarter(reference_date: date | None = None) -> tuple[int, int]:
    """Return (year, quarter) for ``reference_date`` (default today).

    Quarter is 1-based: Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep,
    Q4 = Oct-Dec.
    """

    ref = reference_date or date.today()
    quarter = (ref.month - 1) // 3 + 1
    return ref.year, quarter


def _substitute_review_metadata(
    template_text: str,
    engagement_code: str,
    record: DeploymentRecord,
    year: int,
    quarter: int,
) -> str:
    """Substitute review-prep metadata into the template text."""

    text = template_text

    # Substitute placeholders independently so we don't depend on the
    # exact title-line composition (which can vary between template
    # revisions).
    text = text.replace("[YYYY Q#]", f"{year}Q{quarter}")
    text = text.replace("[ENGAGEMENT CODE]", engagement_code)

    # Methodology version field.
    text = re.sub(
        r"\*\*Methodology version at this review:\*\* \[version\]",
        f"**Methodology version at this review:** "
        f"{record.methodology_version}",
        text,
    )
    text = re.sub(
        r"\*\*Hetarios chassis version:\*\* \[version\]",
        f"**Hetarios chassis version:** {record.hetarios_version}",
        text,
    )

    return text


def scaffold_review_prep(
    cp: ControlPlaneRoot,
    engagement_code: str,
    *,
    year: int | None = None,
    quarter: int | None = None,
    overwrite: bool = False,
) -> ReviewPrepResult:
    """Create a per-quarter review prep file for the engagement.

    If ``year`` and ``quarter`` are not provided, derive from today.

    Raises :class:`ReviewPrepError` if the engagement does not exist,
    the template is missing, or the target file already exists and
    ``overwrite`` is False.
    """

    deployment_path = cp.deployments_dir / f"{engagement_code}.yaml"
    if not deployment_path.is_file():
        raise ReviewPrepError(
            f"deployment record not found for {engagement_code!r}"
        )

    record, report = load_deployment(deployment_path)
    if record is None:
        msgs = "; ".join(i.message for i in report.errors)
        raise ReviewPrepError(
            f"deployment record for {engagement_code!r} did not parse: {msgs}"
        )

    workspace_dir = cp.workspaces_dir / engagement_code
    if not workspace_dir.is_dir():
        raise ReviewPrepError(
            f"workspace directory not found: {workspace_dir}"
        )

    template_path = workspace_dir / "quarterly_review_prep_template.md"
    if not template_path.is_file():
        raise ReviewPrepError(
            f"template not found at {template_path}; was the workspace "
            f"scaffolded with the current control plane version?"
        )

    if year is None or quarter is None:
        derived_year, derived_quarter = determine_quarter()
        year = year if year is not None else derived_year
        quarter = quarter if quarter is not None else derived_quarter

    if not (1 <= quarter <= 4):
        raise ReviewPrepError(f"quarter must be 1..4, got {quarter}")

    output_filename = f"quarterly_review_{year}Q{quarter}.md"
    output_path = workspace_dir / output_filename

    if output_path.exists() and not overwrite:
        raise ReviewPrepError(
            f"{output_path} already exists; pass overwrite=True to replace"
        )

    template_text = template_path.read_text(encoding="utf-8")
    new_text = _substitute_review_metadata(
        template_text, engagement_code, record, year, quarter
    )
    output_path.write_text(new_text, encoding="utf-8")

    return ReviewPrepResult(
        engagement_code=engagement_code,
        review_year=year,
        review_quarter=quarter,
        output_path=output_path,
    )
