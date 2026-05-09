"""Shared pytest fixtures.

The fixture strategy: build a fresh, minimal control plane root in a
tmp_path for each test that needs one. The root has the four marker
directories, the deployment template, the workspace template, the
methodology changelog with one version (0.5.0), and an empty overlay
registry.

This keeps tests isolated from one another and from any control plane
in the developer's working directory.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from aletheia_control_plane.paths import ControlPlaneRoot


# A minimal valid deployment record dict, used as the basis for tests.
def make_valid_record_dict(**overrides) -> dict:
    base: dict = {
        "engagement_code": "test_engagement_2026",
        "client_legal_name": "Test Client Inc.",
        "system_id": "SYS-TEST-001",
        "system_name": "Test System",
        "deployment_date": date(2026, 1, 15),
        "hetarios_version": "0.5.0",
        "methodology_version": "0.5.0",
        "jurisdictions": ["FDA"],
        "trust_domains": ["audit_trail", "model_validation"],
        "overlay_id": None,
        "last_self_test_verified": date(2026, 1, 16),
        "last_interaction_date": date(2026, 1, 20),
        "cadence": "quarterly",
        "phase": "active",
        "retainer_tier": "standard",
        "notes": "Test engagement.",
        "primary_contact": {
            "name": "Jane Smith",
            "role": "Director of Compliance",
            "email": "jane@example.com",
        },
        "workspace_path": "engagement_workspaces/test_engagement_2026/",
    }
    base.update(overrides)
    return base


_DEPLOYMENT_TEMPLATE = dedent(
    """
    engagement_code: ""
    client_legal_name: ""
    system_id: ""
    system_name: ""
    deployment_date: ""
    hetarios_version: ""
    methodology_version: ""
    jurisdictions:
      - ""
    trust_domains:
      - ""
    overlay_id: null
    last_self_test_verified: null
    last_interaction_date: null
    cadence: "quarterly"
    phase: "onboarding"
    retainer_tier: "none"
    notes: ""
    primary_contact:
      name: ""
      role: ""
      email: ""
    workspace_path: "engagement_workspaces/<engagement_code>/"
    """
).lstrip()


_CHANGELOG_TEXT = dedent(
    """
    # Methodology Changelog

    ## v0.5.0 (current shipped) — Test fixture

    Test methodology release.

    ## v0.4.0 — Earlier test version

    Earlier test methodology release.
    """
).lstrip()


_OVERLAY_REGISTRY_TEXT = dedent(
    """
    # Methodology Overlay Registry

    ## Active overlays

    (none)
    """
).lstrip()


_OVERLAY_REGISTRY_WITH_OVERLAY = dedent(
    """
    # Methodology Overlay Registry

    ## Active overlays

    ### overlay-001-test-overlay

    - **Engagement:** test_engagement_2026
    - **Created:** 2026-01-15
    """
).lstrip()


_WORKSPACE_TEMPLATE_FILES: dict[str, str] = {
    "engagement_overview.md": "# Engagement Overview — [ENGAGEMENT CODE]\n",
    "deployment_record.yaml": _DEPLOYMENT_TEMPLATE,
    "quarterly_review_prep_template.md": dedent(
        """
        # Quarterly Review Prep — [ENGAGEMENT CODE] [YYYY Q#]

        ## Review metadata

        - **Methodology version at this review:** [version]
        - **Hetarios chassis version:** [version]
        """
    ).lstrip(),
    "findings_status.md": "# Findings Status — [ENGAGEMENT CODE]\n",
    "methodology_evolution_notes.md": "# Methodology Evolution Notes — [ENGAGEMENT CODE]\n",
    "action_items.md": "# Action Items — [ENGAGEMENT CODE]\n",
    "communications_log.md": "# Communications Log — [ENGAGEMENT CODE]\n",
}


@pytest.fixture
def control_plane(tmp_path: Path) -> ControlPlaneRoot:
    """Build a minimal control plane root in tmp_path."""

    root = tmp_path / "test_cp"
    root.mkdir()

    # Marker directories.
    (root / "deployments").mkdir()
    (root / "engagement_workspaces").mkdir()
    (root / "methodology_releases").mkdir()
    (root / "procedures").mkdir()

    # Deployment template.
    (root / "deployments" / "_template_deployment.yaml").write_text(
        _DEPLOYMENT_TEMPLATE, encoding="utf-8"
    )

    # Workspace template.
    template_dir = root / "engagement_workspaces" / "_template"
    template_dir.mkdir()
    for name, content in _WORKSPACE_TEMPLATE_FILES.items():
        (template_dir / name).write_text(content, encoding="utf-8")

    # Methodology releases.
    (root / "methodology_releases" / "changelog.md").write_text(
        _CHANGELOG_TEXT, encoding="utf-8"
    )
    (root / "methodology_releases" / "overlay_registry.md").write_text(
        _OVERLAY_REGISTRY_TEXT, encoding="utf-8"
    )

    return ControlPlaneRoot(root=root)


@pytest.fixture
def control_plane_with_overlay(control_plane: ControlPlaneRoot) -> ControlPlaneRoot:
    """Control plane with one registered overlay."""

    control_plane.overlay_registry_path.write_text(
        _OVERLAY_REGISTRY_WITH_OVERLAY, encoding="utf-8"
    )
    return control_plane


def write_deployment(
    cp: ControlPlaneRoot,
    record_dict: dict,
    create_workspace: bool = True,
    mirror_matches: bool = True,
) -> Path:
    """Write a deployment file under cp and optionally create the workspace.

    If ``mirror_matches`` is False, the workspace mirror is created with
    a different ``client_legal_name`` so consistency tests can detect
    the drift.
    """

    code = record_dict["engagement_code"]
    deployment_path = cp.deployments_dir / f"{code}.yaml"
    # Convert dates to ISO strings; YAML will round-trip them as such.
    serializable = {}
    for k, v in record_dict.items():
        if isinstance(v, date):
            serializable[k] = v.isoformat()
        else:
            serializable[k] = v
    deployment_path.write_text(
        yaml.safe_dump(serializable, sort_keys=False), encoding="utf-8"
    )

    if create_workspace:
        workspace_dir = cp.workspaces_dir / code
        workspace_dir.mkdir()
        # Copy each template file in.
        for name, content in _WORKSPACE_TEMPLATE_FILES.items():
            (workspace_dir / name).write_text(
                content.replace("[ENGAGEMENT CODE]", code), encoding="utf-8"
            )
        # Write the workspace mirror.
        mirror_data = dict(serializable)
        if not mirror_matches:
            mirror_data["client_legal_name"] = "Drifted Mirror Inc."
        (workspace_dir / "deployment_record.yaml").write_text(
            yaml.safe_dump(mirror_data, sort_keys=False), encoding="utf-8"
        )

    return deployment_path
