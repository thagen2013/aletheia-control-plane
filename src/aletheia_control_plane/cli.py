"""Click-based CLI entry point.

Subcommands:

* ``aletheia-cp validate`` — validate all engagements
* ``aletheia-cp validate <engagement>`` — validate one engagement
* ``aletheia-cp new <engagement-code>`` — scaffold a new engagement
* ``aletheia-cp registry`` — table of all engagements
* ``aletheia-cp methodology-status`` — methodology version status
* ``aletheia-cp prep-review <engagement>`` — scaffold a review prep file
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from aletheia_control_plane import __version__
from aletheia_control_plane.methodology_status import (
    compute_status,
    find_stale_engagements,
    render_status_table,
)
from aletheia_control_plane.paths import (
    ControlPlaneNotFoundError,
    resolve_root,
)
from aletheia_control_plane.registry import (
    collect_entries,
    render_summary,
    render_table,
)
from aletheia_control_plane.review_prep import (
    ReviewPrepError,
    scaffold_review_prep,
)
from aletheia_control_plane.scaffolding import (
    ScaffoldError,
    scaffold_new_engagement,
)
from aletheia_control_plane.schema import Phase
from aletheia_control_plane.validate import (
    validate_engagement,
    validate_root,
)


@click.group(invoke_without_command=False)
@click.version_option(version=__version__, prog_name="aletheia-cp")
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to the control plane root (default: walk up from cwd).",
)
@click.pass_context
def cli(ctx: click.Context, root: Path | None) -> None:
    """Operator CLI for the Aletheia consultant control plane."""

    try:
        cp = resolve_root(root)
    except ControlPlaneNotFoundError as exc:
        click.echo(f"error: {exc}", err=True)
        ctx.exit(2)
    ctx.obj = cp


@cli.command()
@click.argument("engagement_code", required=False)
@click.pass_obj
def validate(cp, engagement_code: str | None) -> None:
    """Validate all engagements (or one if specified)."""

    console = Console()
    if engagement_code is None:
        report = validate_root(cp)
    else:
        report = validate_engagement(cp, engagement_code)

    if not report.issues:
        console.print("[green]ok[/green] — no issues")
        return

    for issue in report.issues:
        if issue.severity.value == "error":
            console.print(f"[red]{issue.render()}[/red]")
        else:
            console.print(f"[yellow]{issue.render()}[/yellow]")

    if report.ok:
        console.print(
            f"\n[yellow]{len(report.warnings)} warning(s)[/yellow]"
        )
    else:
        console.print(
            f"\n[red]{len(report.errors)} error(s)[/red], "
            f"[yellow]{len(report.warnings)} warning(s)[/yellow]"
        )
        sys.exit(1)


@cli.command()
@click.argument("engagement_code")
@click.pass_obj
def new(cp, engagement_code: str) -> None:
    """Scaffold a new engagement workspace and deployment record."""

    console = Console()
    try:
        result = scaffold_new_engagement(cp, engagement_code)
    except ScaffoldError as exc:
        console.print(f"[red]error:[/red] {exc}")
        sys.exit(1)

    console.print(
        f"[green]scaffolded[/green] engagement "
        f"[bold]{result.engagement_code}[/bold]"
    )
    console.print(f"  deployment record: {result.deployment_path}")
    console.print(f"  workspace dir:     {result.workspace_dir}")
    console.print(f"  files created:     {len(result.files_created)}")
    console.print(
        "\nnext steps: fill required fields in the deployment record and "
        "engagement_overview.md, then run "
        f"`aletheia-cp validate {engagement_code}`"
    )


@cli.command()
@click.option(
    "--phase",
    "phase_filter",
    type=click.Choice([p.value for p in Phase]),
    multiple=True,
    help="Filter to one or more phases (default: all).",
)
@click.pass_obj
def registry(cp, phase_filter: tuple[str, ...]) -> None:
    """Show a table of all engagements."""

    from aletheia_control_plane.registry import filter_entries

    console = Console()
    entries = collect_entries(cp)
    if phase_filter:
        phases = {Phase(p) for p in phase_filter}
        entries = filter_entries(entries, include_phases=phases)

    if not entries:
        console.print(
            "[yellow]no engagements found[/yellow] "
            "(no deployment records under deployments/)"
        )
        return

    render_table(entries, console=console)
    summary = render_summary(entries)
    console.print(
        f"\n{summary['total']} engagement(s); "
        f"parse errors: {summary['parse_errors']}"
    )


@cli.command(name="methodology-status")
@click.pass_obj
def methodology_status(cp) -> None:
    """Show methodology version status across all engagements."""

    console = Console()
    entries, current, known = compute_status(cp)

    if not entries:
        console.print("[yellow]no engagements found[/yellow]")
        return

    if not known:
        console.print(
            "[yellow]warning:[/yellow] no methodology versions parsed "
            f"from {cp.changelog_path.name}"
        )

    render_status_table(entries, current, console=console)

    stale = find_stale_engagements(entries)
    if stale:
        console.print(
            f"\n[yellow]{len(stale)} engagement(s) behind current shipped "
            f"version (v{current})[/yellow]"
        )
        for entry in stale:
            console.print(
                f"  - {entry.engagement_code} "
                f"(on v{entry.deployed_version})"
            )


@cli.command(name="prep-review")
@click.argument("engagement_code")
@click.option(
    "--year",
    type=int,
    default=None,
    help="Review year (default: current calendar year).",
)
@click.option(
    "--quarter",
    type=int,
    default=None,
    help="Review quarter 1-4 (default: derived from current date).",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite an existing prep file for the same quarter.",
)
@click.pass_obj
def prep_review(
    cp,
    engagement_code: str,
    year: int | None,
    quarter: int | None,
    overwrite: bool,
) -> None:
    """Scaffold a quarterly review prep file."""

    console = Console()
    try:
        result = scaffold_review_prep(
            cp,
            engagement_code,
            year=year,
            quarter=quarter,
            overwrite=overwrite,
        )
    except ReviewPrepError as exc:
        console.print(f"[red]error:[/red] {exc}")
        sys.exit(1)

    console.print(
        f"[green]scaffolded[/green] review prep for "
        f"[bold]{result.engagement_code}[/bold] "
        f"{result.review_year}Q{result.review_quarter}"
    )
    console.print(f"  output: {result.output_path}")


if __name__ == "__main__":  # pragma: no cover
    cli()
