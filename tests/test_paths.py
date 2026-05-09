"""Tests for paths.py — finding the control plane root."""

from __future__ import annotations

from pathlib import Path

import pytest

from aletheia_control_plane.paths import (
    ControlPlaneNotFoundError,
    ControlPlaneRoot,
    find_root,
    is_control_plane_root,
    resolve_root,
)


def test_is_control_plane_root_true_for_real_root(control_plane):
    assert is_control_plane_root(control_plane.root) is True


def test_is_control_plane_root_false_for_empty_dir(tmp_path):
    assert is_control_plane_root(tmp_path) is False


def test_is_control_plane_root_false_for_nonexistent(tmp_path):
    assert is_control_plane_root(tmp_path / "nonexistent") is False


def test_is_control_plane_root_false_for_partial_markers(tmp_path):
    (tmp_path / "deployments").mkdir()
    # missing the others
    assert is_control_plane_root(tmp_path) is False


def test_is_control_plane_root_false_for_file(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("not a directory")
    assert is_control_plane_root(f) is False


def test_find_root_walks_up(control_plane):
    nested = control_plane.root / "engagement_workspaces" / "_template"
    found = find_root(start=nested)
    assert found.root == control_plane.root


def test_find_root_returns_self_when_at_root(control_plane):
    found = find_root(start=control_plane.root)
    assert found.root == control_plane.root


def test_find_root_raises_when_no_markers(tmp_path):
    with pytest.raises(ControlPlaneNotFoundError) as exc_info:
        find_root(start=tmp_path)
    assert "No control plane root found" in str(exc_info.value)


def test_resolve_root_uses_explicit(control_plane):
    found = resolve_root(control_plane.root)
    assert found.root == control_plane.root


def test_resolve_root_explicit_invalid_raises(tmp_path):
    with pytest.raises(ControlPlaneNotFoundError) as exc_info:
        resolve_root(tmp_path)
    assert "does not look like a control plane root" in str(exc_info.value)


def test_resolve_root_falls_back_to_cwd(control_plane, monkeypatch):
    monkeypatch.chdir(control_plane.root)
    found = resolve_root(None)
    assert found.root == control_plane.root


def test_control_plane_root_derived_paths(control_plane):
    assert control_plane.deployments_dir == control_plane.root / "deployments"
    assert control_plane.workspaces_dir == control_plane.root / "engagement_workspaces"
    assert (
        control_plane.methodology_releases_dir
        == control_plane.root / "methodology_releases"
    )
    assert control_plane.procedures_dir == control_plane.root / "procedures"
    assert (
        control_plane.changelog_path
        == control_plane.root / "methodology_releases" / "changelog.md"
    )
    assert (
        control_plane.overlay_registry_path
        == control_plane.root / "methodology_releases" / "overlay_registry.md"
    )
    assert (
        control_plane.deployment_template_path
        == control_plane.root / "deployments" / "_template_deployment.yaml"
    )
    assert (
        control_plane.workspace_template_dir
        == control_plane.root / "engagement_workspaces" / "_template"
    )
