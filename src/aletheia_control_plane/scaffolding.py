"""Scaffold a new engagement workspace from templates.

Creates ``deployments/<code>.yaml`` from the deployment template, and
``engagement_workspaces/<code>/`` from the workspace template tree.

The template files contain placeholder strings; this module substitutes
the engagement code into the placeholders so the new files are at
least starting-point valid (the operator still has to fill client
name, system_id, contact, etc.).
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from aletheia_control_plane.paths import ControlPlaneRoot


_PLACEHOLDER_ENGAGEMENT_CODE_BRACKETS = "[ENGAGEMENT CODE]"
_PLACEHOLDER_ENGAGEMENT_CODE_ANGLES = "<engagement_code>"


class ScaffoldError(RuntimeError):
    """Raised when scaffolding fails (e.g. engagement code already exists)."""


@dataclass
class ScaffoldResult:
    """Result of a scaffolding operation."""

    engagement_code: str
    deployment_path: Path
    workspace_dir: Path
    files_created: list[Path]


_ENGAGEMENT_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]+$")


def _validate_engagement_code(code: str) -> None:
    if not _ENGAGEMENT_CODE_PATTERN.match(code):
        raise ScaffoldError(
            f"engagement_code {code!r} is not valid: must start with a "
            f"lowercase letter and contain only lowercase letters, digits, "
            f"and underscores"
        )
    if len(code) < 3:
        raise ScaffoldError(
            f"engagement_code {code!r} is too short (minimum 3 characters)"
        )
    if len(code) > 64:
        raise ScaffoldError(
            f"engagement_code {code!r} is too long (maximum 64 characters)"
        )


def _ensure_no_collision(cp: ControlPlaneRoot, code: str) -> None:
    deployment_path = cp.deployments_dir / f"{code}.yaml"
    if deployment_path.exists():
        raise ScaffoldError(
            f"deployment record already exists at {deployment_path}; "
            f"choose a different engagement code or remove the existing record"
        )
    workspace_dir = cp.workspaces_dir / code
    if workspace_dir.exists():
        raise ScaffoldError(
            f"workspace directory already exists at {workspace_dir}; "
            f"choose a different engagement code or remove the existing workspace"
        )


def _substitute_placeholders(content: str, engagement_code: str) -> str:
    """Substitute engagement-code placeholders in template content."""

    content = content.replace(
        _PLACEHOLDER_ENGAGEMENT_CODE_BRACKETS, engagement_code
    )
    content = content.replace(
        _PLACEHOLDER_ENGAGEMENT_CODE_ANGLES, engagement_code
    )
    return content


def _write_with_substitution(
    src: Path, dst: Path, engagement_code: str
) -> None:
    text = src.read_text(encoding="utf-8")
    new_text = _substitute_placeholders(text, engagement_code)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(new_text, encoding="utf-8")


def _seed_deployment_record(
    template_path: Path, target_path: Path, engagement_code: str
) -> None:
    """Write a new deployment record from the template.

    Substitutes the engagement code into the workspace_path field and
    the engagement_code field. The result is not yet a valid record
    (other required fields are still empty); the operator fills those
    in before the next ``aletheia-cp validate`` will pass.
    """

    text = template_path.read_text(encoding="utf-8")
    # Replace empty engagement_code with the new value.
    text = re.sub(
        r'^engagement_code:\s*""',
        f'engagement_code: "{engagement_code}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    # Replace the workspace_path placeholder.
    text = text.replace(
        'workspace_path: "engagement_workspaces/<engagement_code>/"',
        f'workspace_path: "engagement_workspaces/{engagement_code}/"',
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(text, encoding="utf-8")


def scaffold_new_engagement(
    cp: ControlPlaneRoot, engagement_code: str
) -> ScaffoldResult:
    """Create a new engagement deployment record and workspace.

    Steps:

    1. Validate engagement_code format
    2. Check for collisions
    3. Copy the deployment template to ``deployments/<code>.yaml``,
       substituting placeholders
    4. Recursively copy the workspace template to
       ``engagement_workspaces/<code>/``, substituting placeholders
    5. Return a result describing what was created
    """

    _validate_engagement_code(engagement_code)
    _ensure_no_collision(cp, engagement_code)

    if not cp.deployment_template_path.is_file():
        raise ScaffoldError(
            f"deployment template not found at {cp.deployment_template_path}"
        )
    if not cp.workspace_template_dir.is_dir():
        raise ScaffoldError(
            f"workspace template not found at {cp.workspace_template_dir}"
        )

    files_created: list[Path] = []

    # 1. Deployment record.
    deployment_path = cp.deployments_dir / f"{engagement_code}.yaml"
    _seed_deployment_record(
        cp.deployment_template_path, deployment_path, engagement_code
    )
    files_created.append(deployment_path)

    # 2. Workspace tree.
    workspace_dir = cp.workspaces_dir / engagement_code
    workspace_dir.mkdir(parents=True, exist_ok=False)

    template_root = cp.workspace_template_dir
    for src in sorted(template_root.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(template_root)
        dst = workspace_dir / rel
        _write_with_substitution(src, dst, engagement_code)
        files_created.append(dst)

    # 3. Mirror the deployment record into the workspace.
    workspace_mirror = workspace_dir / "deployment_record.yaml"
    _seed_deployment_record(
        cp.deployment_template_path, workspace_mirror, engagement_code
    )
    if workspace_mirror not in files_created:
        files_created.append(workspace_mirror)

    return ScaffoldResult(
        engagement_code=engagement_code,
        deployment_path=deployment_path,
        workspace_dir=workspace_dir,
        files_created=files_created,
    )


def remove_engagement(
    cp: ControlPlaneRoot, engagement_code: str
) -> tuple[Path, Path]:
    """Remove a scaffolded engagement (used by tests and recovery).

    Returns the deployment path and workspace dir that were removed.
    Raises FileNotFoundError if neither exists.
    """

    deployment_path = cp.deployments_dir / f"{engagement_code}.yaml"
    workspace_dir = cp.workspaces_dir / engagement_code

    if not deployment_path.exists() and not workspace_dir.exists():
        raise FileNotFoundError(
            f"no engagement found for code {engagement_code!r}"
        )

    if deployment_path.exists():
        deployment_path.unlink()
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)

    return deployment_path, workspace_dir
