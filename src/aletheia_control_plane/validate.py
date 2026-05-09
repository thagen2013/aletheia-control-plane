"""Cross-reference validator for the control plane.

Validates that every deployment record is internally well-formed and
that every cross-reference between deployments, workspaces, methodology
releases, and overlays resolves correctly.

Entry points:

* :func:`validate_root` — validate everything under a control plane root
* :func:`validate_engagement` — validate a single engagement (deployment + workspace)
* :func:`load_deployment` — load a single deployment YAML and parse it
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from aletheia_control_plane.paths import ControlPlaneRoot
from aletheia_control_plane.schema import (
    DeploymentRecord,
    is_template_engagement_code,
)


# --- result types -------------------------------------------------------


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    """A single validation issue."""

    severity: Severity
    message: str
    file_path: Path | None = None
    field_path: str | None = None

    def render(self) -> str:
        bits: list[str] = [f"[{self.severity.value}]"]
        if self.file_path is not None:
            bits.append(str(self.file_path))
        if self.field_path is not None:
            bits.append(f"({self.field_path})")
        bits.append(self.message)
        return " ".join(bits)


@dataclass
class ValidationReport:
    """Aggregated result of a validation run."""

    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add(
        self,
        severity: Severity,
        message: str,
        file_path: Path | None = None,
        field_path: str | None = None,
    ) -> None:
        self.issues.append(
            Issue(
                severity=severity,
                message=message,
                file_path=file_path,
                field_path=field_path,
            )
        )

    def merge(self, other: ValidationReport) -> None:
        self.issues.extend(other.issues)


# --- helpers ------------------------------------------------------------


def load_yaml(path: Path) -> dict[str, Any] | None:
    """Load a YAML file, returning None if the file is empty or all-null."""

    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top-level YAML value is not a mapping (got {type(data).__name__})"
        )
    return data


def discover_deployments(cp: ControlPlaneRoot) -> list[Path]:
    """Return the deployment YAML files (excluding template)."""

    return sorted(
        p
        for p in cp.deployments_dir.glob("*.yaml")
        if not p.name.startswith("_")
    )


def discover_engagement_workspaces(cp: ControlPlaneRoot) -> list[Path]:
    """Return per-engagement workspace directories (excluding template)."""

    return sorted(
        p
        for p in cp.workspaces_dir.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


_VERSION_HEADER_RE = re.compile(r"^##\s+(v?\d+\.\d+\.\d+(?:-[a-z0-9.]+)?)\b")


def parse_methodology_versions(changelog_path: Path) -> set[str]:
    """Parse methodology versions from the changelog.

    Looks for lines like ``## v0.5.0 ...`` or ``## 0.5.0 ...``. Returns
    versions normalized without leading ``v``.
    """

    if not changelog_path.is_file():
        return set()
    versions: set[str] = set()
    for line in changelog_path.read_text(encoding="utf-8").splitlines():
        match = _VERSION_HEADER_RE.match(line)
        if match:
            v = match.group(1)
            v = v.removeprefix("v")
            versions.add(v)
    return versions


_OVERLAY_HEADER_RE = re.compile(r"^###\s+(overlay-\d+-[a-z0-9-]+)")


def parse_overlay_ids(overlay_registry_path: Path) -> set[str]:
    """Parse overlay IDs from the overlay registry."""

    if not overlay_registry_path.is_file():
        return set()
    overlay_ids: set[str] = set()
    for line in overlay_registry_path.read_text(encoding="utf-8").splitlines():
        match = _OVERLAY_HEADER_RE.match(line)
        if match:
            overlay_ids.add(match.group(1))
    return overlay_ids


# --- single-deployment validation ---------------------------------------


def load_deployment(path: Path) -> tuple[DeploymentRecord | None, ValidationReport]:
    """Load and parse a deployment YAML file.

    Returns a tuple of (record, report). The record is None when
    parsing fails (in which case the report carries the error).
    """

    report = ValidationReport()
    try:
        data = load_yaml(path)
    except yaml.YAMLError as exc:
        report.add(Severity.ERROR, f"YAML parse error: {exc}", file_path=path)
        return None, report
    except ValueError as exc:
        report.add(Severity.ERROR, str(exc), file_path=path)
        return None, report

    if data is None:
        report.add(
            Severity.ERROR,
            "deployment record is empty",
            file_path=path,
        )
        return None, report

    code = data.get("engagement_code", "")
    if is_template_engagement_code(code):
        report.add(
            Severity.ERROR,
            "engagement_code is empty or placeholder; this looks like an unfilled template",
            file_path=path,
            field_path="engagement_code",
        )
        return None, report

    try:
        record = DeploymentRecord.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            field_path = ".".join(str(loc) for loc in err["loc"])
            report.add(
                Severity.ERROR,
                err["msg"],
                file_path=path,
                field_path=field_path,
            )
        return None, report

    return record, report


# --- mirror consistency ------------------------------------------------


def _compare_records(
    canonical: dict[str, Any],
    mirror: dict[str, Any],
) -> list[str]:
    """Return list of fields that differ between canonical and mirror."""

    differing: list[str] = []
    all_keys = set(canonical.keys()) | set(mirror.keys())
    for key in sorted(all_keys):
        if canonical.get(key) != mirror.get(key):
            differing.append(key)
    return differing


def validate_workspace_mirror(
    deployment_path: Path,
    workspace_dir: Path,
) -> ValidationReport:
    """Validate that the workspace deployment_record.yaml matches canonical."""

    report = ValidationReport()
    mirror_path = workspace_dir / "deployment_record.yaml"
    if not mirror_path.is_file():
        report.add(
            Severity.ERROR,
            f"workspace mirror missing at {mirror_path}",
            file_path=workspace_dir,
        )
        return report

    try:
        canonical_data = load_yaml(deployment_path)
        mirror_data = load_yaml(mirror_path)
    except (yaml.YAMLError, ValueError) as exc:
        report.add(
            Severity.ERROR,
            f"YAML parse error in mirror comparison: {exc}",
            file_path=mirror_path,
        )
        return report

    if canonical_data is None or mirror_data is None:
        report.add(
            Severity.ERROR,
            "one of the records is empty; cannot compare",
            file_path=mirror_path,
        )
        return report

    differing = _compare_records(canonical_data, mirror_data)
    if differing:
        for key in differing:
            report.add(
                Severity.ERROR,
                f"workspace mirror field {key!r} differs from canonical "
                f"deployment record",
                file_path=mirror_path,
                field_path=key,
            )
    return report


# --- top-level validation ----------------------------------------------


def validate_root(cp: ControlPlaneRoot) -> ValidationReport:
    """Validate every deployment, workspace, and cross-reference under root."""

    report = ValidationReport()

    methodology_versions = parse_methodology_versions(cp.changelog_path)
    if not methodology_versions:
        report.add(
            Severity.WARNING,
            "no methodology versions parsed from changelog "
            "(any deployment will fail methodology_version validation)",
            file_path=cp.changelog_path,
        )

    overlay_ids = parse_overlay_ids(cp.overlay_registry_path)

    deployment_paths = discover_deployments(cp)
    workspace_dirs = discover_engagement_workspaces(cp)
    workspace_dirs_by_name = {d.name: d for d in workspace_dirs}

    seen_codes: dict[str, Path] = {}
    # Track every deployment filename's stem regardless of whether it parsed.
    # Used to suppress "workspace has no corresponding deployment" when the
    # deployment file exists but failed to parse.
    deployment_filename_stems: set[str] = {p.stem for p in deployment_paths}

    for deployment_path in deployment_paths:
        record, sub_report = load_deployment(deployment_path)
        report.merge(sub_report)
        if record is None:
            continue

        # Engagement code uniqueness across deployments.
        if record.engagement_code in seen_codes:
            report.add(
                Severity.ERROR,
                f"engagement_code {record.engagement_code!r} also defined "
                f"in {seen_codes[record.engagement_code]}",
                file_path=deployment_path,
                field_path="engagement_code",
            )
        else:
            seen_codes[record.engagement_code] = deployment_path

        # Filename should match engagement_code.
        expected_filename = f"{record.engagement_code}.yaml"
        if deployment_path.name != expected_filename:
            report.add(
                Severity.ERROR,
                f"deployment filename {deployment_path.name!r} does not match "
                f"engagement_code {record.engagement_code!r} "
                f"(expected {expected_filename!r})",
                file_path=deployment_path,
                field_path="engagement_code",
            )

        # Methodology version must exist in changelog.
        normalized_version = record.methodology_version.removeprefix("v")
        if methodology_versions and normalized_version not in methodology_versions:
            report.add(
                Severity.ERROR,
                f"methodology_version {record.methodology_version!r} does not "
                f"appear in {cp.changelog_path.name} "
                f"(known versions: {sorted(methodology_versions)})",
                file_path=deployment_path,
                field_path="methodology_version",
            )

        # Overlay must exist if set.
        if record.overlay_id is not None:
            if record.overlay_id not in overlay_ids:
                report.add(
                    Severity.ERROR,
                    f"overlay_id {record.overlay_id!r} does not appear in "
                    f"{cp.overlay_registry_path.name}",
                    file_path=deployment_path,
                    field_path="overlay_id",
                )

        # Workspace directory must exist.
        workspace_dir = workspace_dirs_by_name.get(record.engagement_code)
        if workspace_dir is None:
            report.add(
                Severity.ERROR,
                f"engagement workspace directory not found: "
                f"engagement_workspaces/{record.engagement_code}/",
                file_path=deployment_path,
                field_path="engagement_code",
            )
        else:
            mirror_report = validate_workspace_mirror(
                deployment_path, workspace_dir
            )
            report.merge(mirror_report)

    # Workspace directories without a corresponding deployment file.
    # We use deployment_filename_stems (existence on disk) rather than
    # seen_codes (successfully parsed) so a workspace whose deployment
    # exists but fails to parse is not double-reported.
    for workspace_dir in workspace_dirs:
        if workspace_dir.name not in deployment_filename_stems:
            report.add(
                Severity.ERROR,
                f"workspace directory has no corresponding deployment record "
                f"in deployments/{workspace_dir.name}.yaml",
                file_path=workspace_dir,
            )

    return report


def validate_engagement(
    cp: ControlPlaneRoot, engagement_code: str
) -> ValidationReport:
    """Validate a single engagement by code."""

    report = ValidationReport()
    deployment_path = cp.deployments_dir / f"{engagement_code}.yaml"
    if not deployment_path.is_file():
        report.add(
            Severity.ERROR,
            f"deployment file not found: {deployment_path}",
        )
        return report

    record, sub_report = load_deployment(deployment_path)
    report.merge(sub_report)
    if record is None:
        return report

    methodology_versions = parse_methodology_versions(cp.changelog_path)
    overlay_ids = parse_overlay_ids(cp.overlay_registry_path)

    normalized_version = record.methodology_version.removeprefix("v")
    if methodology_versions and normalized_version not in methodology_versions:
        report.add(
            Severity.ERROR,
            f"methodology_version {record.methodology_version!r} does not "
            f"appear in {cp.changelog_path.name}",
            file_path=deployment_path,
            field_path="methodology_version",
        )

    if record.overlay_id is not None and record.overlay_id not in overlay_ids:
        report.add(
            Severity.ERROR,
            f"overlay_id {record.overlay_id!r} does not appear in "
            f"{cp.overlay_registry_path.name}",
            file_path=deployment_path,
            field_path="overlay_id",
        )

    workspace_dir = cp.workspaces_dir / engagement_code
    if not workspace_dir.is_dir():
        report.add(
            Severity.ERROR,
            f"workspace directory not found: {workspace_dir}",
        )
    else:
        mirror_report = validate_workspace_mirror(deployment_path, workspace_dir)
        report.merge(mirror_report)

    return report
