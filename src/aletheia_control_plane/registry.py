"""Registry view: a table of all active engagements.

Loads every deployment record under the control plane root and renders
a table summary. Useful for quick consultant-side situational awareness
without having to grep through individual YAML files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from aletheia_control_plane.paths import ControlPlaneRoot
from aletheia_control_plane.schema import DeploymentRecord, Phase
from aletheia_control_plane.validate import discover_deployments, load_deployment


@dataclass
class RegistryEntry:
    """One row in the registry view."""

    deployment_path: Path
    record: DeploymentRecord | None
    parse_error: str | None = None


def collect_entries(cp: ControlPlaneRoot) -> list[RegistryEntry]:
    """Load every deployment record into a list of RegistryEntry."""

    entries: list[RegistryEntry] = []
    for path in discover_deployments(cp):
        record, report = load_deployment(path)
        if record is None:
            error_msg = "; ".join(i.message for i in report.errors)
            entries.append(
                RegistryEntry(
                    deployment_path=path,
                    record=None,
                    parse_error=error_msg or "unknown parse error",
                )
            )
        else:
            entries.append(RegistryEntry(deployment_path=path, record=record))
    return entries


def filter_entries(
    entries: list[RegistryEntry],
    *,
    include_phases: set[Phase] | None = None,
) -> list[RegistryEntry]:
    """Return entries whose phase is in ``include_phases``.

    If ``include_phases`` is None, all entries are included.
    Entries that failed to parse are always included (so the operator
    sees them in the table) regardless of phase filter.
    """

    if include_phases is None:
        return list(entries)

    filtered: list[RegistryEntry] = []
    for entry in entries:
        if entry.record is None:
            filtered.append(entry)
            continue
        if entry.record.phase in include_phases:
            filtered.append(entry)
    return filtered


def render_table(
    entries: list[RegistryEntry],
    console: Console | None = None,
) -> Table:
    """Build a rich table from a list of registry entries."""

    table = Table(title="Aletheia Control Plane — Engagements")
    table.add_column("Code", style="bold")
    table.add_column("Client")
    table.add_column("Phase")
    table.add_column("Methodology")
    table.add_column("Hetarios")
    table.add_column("Cadence")
    table.add_column("Retainer")
    table.add_column("Last interaction")

    for entry in entries:
        if entry.record is None:
            table.add_row(
                entry.deployment_path.stem,
                "[red]parse error[/red]",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
            )
            continue
        record = entry.record
        last = (
            record.last_interaction_date.isoformat()
            if record.last_interaction_date is not None
            else "-"
        )
        table.add_row(
            record.engagement_code,
            record.client_legal_name,
            record.phase.value,
            record.methodology_version,
            record.hetarios_version,
            record.cadence.value,
            record.retainer_tier.value,
            last,
        )

    if console is not None:
        console.print(table)
    return table


def render_summary(entries: list[RegistryEntry]) -> dict[str, int]:
    """Return a small summary dict: counts by phase, plus totals."""

    summary: dict[str, int] = {
        "total": len(entries),
        "parse_errors": 0,
    }
    for phase in Phase:
        summary[f"phase_{phase.value}"] = 0
    for entry in entries:
        if entry.record is None:
            summary["parse_errors"] += 1
            continue
        summary[f"phase_{entry.record.phase.value}"] += 1
    return summary
