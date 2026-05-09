"""Pin __version__ in __init__.py to the version declared in pyproject.toml.

Drift between the two means `aletheia-cp --version` reports a different
number from the installed package metadata. Bumping one without the
other has bitten paired repos before; this test catches it for free
on the next bump.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from aletheia_control_plane import __version__


def test_version_in_sync_with_pyproject():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    assert __version__ == pyproject["project"]["version"], (
        f"__version__ in src/aletheia_control_plane/__init__.py "
        f"({__version__!r}) does not match pyproject.toml "
        f"({pyproject['project']['version']!r}). Bump both together."
    )
