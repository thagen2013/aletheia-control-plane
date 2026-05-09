# Methodology Releases

Consultant-side records and procedures for managing methodology
versions across active deployments.

The methodology itself lives in the engine repo (`aletheia-trust-engine`)
under `knowledge_base/*.yaml` files, with version-bump discipline
enforced by `tests/test_methodology_version_drift.py`. This directory
is the *consultant's* record of:

- which methodology versions exist and what changed in each
- which clients are on which methodology version
- which clients have client-specific overlays that the consultant
  must maintain alongside shipped methodology
- the procedure for getting a methodology version released into
  client deployments

## Files in this directory

| File | Purpose |
|---|---|
| `changelog.md` | Methodology version history with what changed in each version |
| `overlay_registry.md` | Client-specific KB overlays (most clients have none) |
| `release_procedure.md` | The consultant procedure for shipping a methodology release |

## What lives where

| Question | Answer location |
|---|---|
| What's in v0.5.0? | `changelog.md` |
| What changed from v0.4.0 to v0.5.0? | `changelog.md` |
| Which client is running v0.4.0 vs v0.5.0? | `deployments/<engagement_code>.yaml` (`methodology_version`) |
| Does this client have an overlay? | `deployments/<engagement_code>.yaml` (`overlay_id`) → cross-reference `overlay_registry.md` |
| How do I push v0.5.0 → v0.5.1 to a client? | `release_procedure.md` |
| What's the source of truth for the methodology itself? | The engine repo's `knowledge_base/` directory, NOT this directory |

## Why a separate consultant-side record

The engine repo's methodology files are the canonical methodology.
The consultant's responsibility is *operational*:

- Knowing which client is on which version, so quarterly reviews
  reference the right invariants and groundings
- Knowing when a methodology bump should land at which client, so
  no deployment runs forever on a stale methodology
- Knowing if a client has overlays that need to be maintained when
  the underlying methodology evolves
- Documenting the release procedure so a second consultant can
  ship a methodology release without ambiguity

This is fleet-aware metadata, not methodology source-of-truth.

## Privacy

The `changelog.md` file contains methodology evolution narrative;
it is not client-confidential. The `overlay_registry.md` file may
reference client engagements by code; treat as confidential.
