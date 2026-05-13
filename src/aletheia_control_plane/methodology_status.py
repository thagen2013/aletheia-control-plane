"""Methodology status across engagements.

Shows which engagements are on which methodology version, identifies
the current shipped version (the highest version in the changelog),
and flags engagements that are behind.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from aletheia_control_plane.paths import ControlPlaneRoot
from aletheia_control_plane.schema import DeploymentRecord, Phase
from aletheia_control_plane.validate import (
    discover_deployments,
    load_deployment,
    parse_methodology_versions,
)


def _semver_tuple(version: str) -> tuple[int, int, int]:
    """Convert a semver string to a sortable tuple.

    Strips a leading ``v`` if present. Pre-release suffixes are
    ignored for ordering (treated as equal to the base version).
    """

    base = version.removeprefix("v")
    base = base.split("-", 1)[0]
    parts = base.split(".")
    if len(parts) != 3:
        raise ValueError(f"not a semver: {version!r}")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def determine_current_version(versions: set[str]) -> str | None:
    """Return the highest version in the set, or None if the set is empty."""

    if not versions:
        return None
    return max(versions, key=_semver_tuple)


@dataclass
class MethodologyStatusEntry:
    """One engagement's methodology status."""

    engagement_code: str
    client: str
    phase: Phase
    deployed_version: str
    current_version: str | None
    is_current: bool
    is_unknown: bool


def compute_status(
    cp: ControlPlaneRoot,
) -> tuple[list[MethodologyStatusEntry], str | None, set[str], list[Path]]:
    """Compute methodology status for every engagement.

    Returns ``(entries, current_version, known_versions, parse_errors)``
    where ``parse_errors`` lists deployment file paths that could not be
    loaded so the caller can surface a fleet-broken state to the operator
    rather than treating it as an empty fleet.

    Classification of ``is_unknown`` uses semver ordering against the
    current shipped version, not membership in ``known_versions``. A
    deployment pinned to a previously-shipped version whose detailed
    changelog entry has been collapsed into a prose ``## Earlier versions``
    section is still classified as ``behind``. Membership-based catalog
    enforcement is the job of ``validate``.
    """

    known_versions = parse_methodology_versions(cp.changelog_path)
    current_version = determine_current_version(known_versions)
    current_tuple = (
        _semver_tuple(current_version) if current_version is not None else None
    )

    entries: list[MethodologyStatusEntry] = []
    parse_errors: list[Path] = []
    for path in discover_deployments(cp):
        record, _ = load_deployment(path)
        if record is None:
            parse_errors.append(path)
            continue
        deployed = record.methodology_version.removeprefix("v")
        is_current = (
            current_version is not None and deployed == current_version
        )
        is_unknown = _classify_unknown(deployed, current_tuple, is_current)
        entries.append(
            MethodologyStatusEntry(
                engagement_code=record.engagement_code,
                client=record.client_legal_name,
                phase=record.phase,
                deployed_version=deployed,
                current_version=current_version,
                is_current=is_current,
                is_unknown=is_unknown,
            )
        )
    return entries, current_version, known_versions, parse_errors


def _classify_unknown(
    deployed: str,
    current_tuple: tuple[int, int, int] | None,
    is_current: bool,
) -> bool:
    """Return True when the deployed version cannot be safely classified.

    ``unknown`` covers: no current version available (no changelog), or
    deployed version ahead of the current shipped version (suspect typo
    or unreleased build). A deployment older than current is NOT
    unknown — it is ``behind``. Schema enforces semver shape, so
    ``deployed`` is always parseable here.
    """

    if is_current:
        return False
    if current_tuple is None:
        return True
    return _semver_tuple(deployed) > current_tuple


def render_status_table(
    entries: list[MethodologyStatusEntry],
    current_version: str | None,
    console: Console | None = None,
) -> Table:
    """Render a methodology-status table."""

    title = "Methodology Status"
    if current_version is not None:
        title += f" — current shipped: v{current_version}"
    table = Table(title=title)
    table.add_column("Code", style="bold")
    table.add_column("Client")
    table.add_column("Phase")
    table.add_column("Deployed version")
    table.add_column("Status")

    for entry in entries:
        if entry.is_unknown:
            status = "[red]unknown version[/red]"
        elif entry.is_current:
            status = "[green]current[/green]"
        else:
            status = "[yellow]behind[/yellow]"
        table.add_row(
            entry.engagement_code,
            entry.client,
            entry.phase.value,
            entry.deployed_version,
            status,
        )

    if console is not None:
        console.print(table)
    return table


def find_stale_engagements(
    entries: list[MethodologyStatusEntry],
) -> list[MethodologyStatusEntry]:
    """Return engagements that are behind the current shipped version.

    Includes only entries where the deployed version is known but not
    current. Engagements with unknown versions are NOT included; they
    should be investigated separately as validation failures.

    Engagements in ``closed`` phase are excluded — closed engagements
    do not require methodology updates.
    """

    stale: list[MethodologyStatusEntry] = []
    for entry in entries:
        if entry.is_unknown:
            continue
        if entry.is_current:
            continue
        if entry.phase is Phase.CLOSED:
            continue
        stale.append(entry)
    return stale
