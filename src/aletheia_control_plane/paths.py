"""Locate the control-plane root directory.

The control plane root is the directory containing the canonical
markers: a ``deployments/`` subdirectory and a ``methodology_releases/``
subdirectory. The CLI walks up from the working directory (or an
explicit ``--root`` argument) until it finds those markers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


CONTROL_PLANE_MARKERS: tuple[str, ...] = (
    "deployments",
    "methodology_releases",
    "engagement_workspaces",
    "procedures",
)


class ControlPlaneNotFoundError(RuntimeError):
    """Raised when no control plane root can be located."""


@dataclass(frozen=True)
class ControlPlaneRoot:
    """Resolved control plane root with derived paths."""

    root: Path

    @property
    def deployments_dir(self) -> Path:
        return self.root / "deployments"

    @property
    def workspaces_dir(self) -> Path:
        return self.root / "engagement_workspaces"

    @property
    def methodology_releases_dir(self) -> Path:
        return self.root / "methodology_releases"

    @property
    def procedures_dir(self) -> Path:
        return self.root / "procedures"

    @property
    def changelog_path(self) -> Path:
        return self.methodology_releases_dir / "changelog.md"

    @property
    def versions_manifest_path(self) -> Path:
        return self.methodology_releases_dir / "versions.yaml"

    @property
    def overlay_registry_path(self) -> Path:
        return self.methodology_releases_dir / "overlay_registry.md"

    @property
    def deployment_template_path(self) -> Path:
        return self.deployments_dir / "_template_deployment.yaml"

    @property
    def workspace_template_dir(self) -> Path:
        return self.workspaces_dir / "_template"


def is_control_plane_root(path: Path) -> bool:
    """Return True if ``path`` looks like a control plane root."""

    if not path.is_dir():
        return False
    return all((path / marker).is_dir() for marker in CONTROL_PLANE_MARKERS)


def find_root(start: Path | None = None) -> ControlPlaneRoot:
    """Walk up from ``start`` (or cwd) to find a control-plane root.

    Raises :class:`ControlPlaneNotFoundError` if no root is found
    before reaching the filesystem root.
    """

    current = (start or Path.cwd()).resolve()
    visited: list[Path] = []
    while True:
        visited.append(current)
        if is_control_plane_root(current):
            return ControlPlaneRoot(root=current)
        parent = current.parent
        if parent == current:
            visited_str = ", ".join(str(p) for p in visited)
            raise ControlPlaneNotFoundError(
                "No control plane root found; checked: " + visited_str
            )
        current = parent


def resolve_root(explicit: Path | None) -> ControlPlaneRoot:
    """Resolve the control plane root from an explicit path or cwd.

    If ``explicit`` is provided and points to a control plane root,
    return that. Otherwise walk up from cwd.
    """

    if explicit is not None:
        explicit = explicit.resolve()
        if is_control_plane_root(explicit):
            return ControlPlaneRoot(root=explicit)
        raise ControlPlaneNotFoundError(
            f"{explicit} does not look like a control plane root "
            f"(missing one of: {', '.join(CONTROL_PLANE_MARKERS)})"
        )
    return find_root()
