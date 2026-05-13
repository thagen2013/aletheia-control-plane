# Methodology Release Procedure

How a methodology version moves from "shipped in the engine repo"
to "running at active client deployments."

This procedure applies to methodology version bumps (v0.5.0 →
v0.5.1, v0.5.0 → v0.6.0, etc.). It does NOT apply to Hetarios
chassis-only updates (those follow `deployment_change_procedure.md`).

## Phase 1: Engine-side release (consultant or upstream maintainer)

1. **Verify the engine release is clean.** The new methodology
   version is tagged in the engine repo. Constitution check passes.
   Test suite passes. Coverage gate (100%) passes. Methodology
   version drift detection passes. Citation integrity passes. Tier
   1 + Tier 2 v2 red-team criteria all PASSING.
2. **Verify byte-stable real cases still byte-equal.** Re-run the
   real-case deep-runs and confirm byte-stable regression tests
   still pass. If any real case drifted, the change requires
   semantic revision (not just version bump) and the deliverable
   bundle's worked examples need to be re-aligned.
3. **Update `methodology_releases/changelog.md`** with a new entry
   describing what's new, engagement implications, open gaps, and
   migration notes.
4. **Update `methodology_releases/versions.yaml`** with a new entry
   for the version. Add fields: `version` (semver string),
   `status` (`engagement-ready` for normal releases,
   `development-tier` for pre-release builds), and `notes` (one-line
   summary). The manifest is what `aletheia-cp validate` consumes;
   forgetting this step will cause every deployment pinned to the
   new version to fail validation.
5. **Re-validate all active overlays** against the new methodology
   per `overlay_registry.md` re-validation procedure. Update overlay
   registry entries with the re-validation timestamp.

At end of Phase 1: the engine repo has a tagged release; the
consultant control plane has a changelog entry and a versions.yaml
manifest entry; overlays are re-validated. No client deployments
have changed yet.

## Phase 2: Per-client rollout decision

For each active deployment in `deployments/`:

1. **Check engagement phase.** A deployment in `closed` phase does
   not need methodology updates. A deployment in `discovery` may
   not have a self-test verified yet. Roll out to `onboarding`,
   `active`, and `transitioning` deployments.
2. **Check methodology delta materiality.** Use the changelog to
   evaluate: does this version bump produce additional findings on
   this client's corpus shape? If yes, the client should know
   before the upgrade lands. If no, the upgrade can be routine.
3. **Check overlay compatibility.** If the deployment has an
   overlay, confirm the overlay re-validation passed for the new
   version.
4. **Decide rollout timing.** Three options:
   - **Quarterly review window** (default): wait until the next
     scheduled quarterly review to roll out, walk the client
     through the changelog, then upgrade together.
   - **Out-of-band priority**: methodology version bump addresses
     a regulatory development that affects this client immediately.
     Communicate to client outside normal cadence and roll out
     ahead of next quarterly review.
   - **Defer**: client is in a sensitive period (mid-submission,
     mid-audit) where additional findings would create operational
     friction. Defer to a window after the sensitive period.

Document the decision per client in their engagement workspace's
`methodology_evolution_notes.md`.

## Phase 3: Per-client rollout execution

For each deployment cleared for rollout:

1. **Notify the client.** Methodology version bumps land at the
   client through git-tag pull on their Hetarios checkout. The
   client's engineering team needs to know.
2. **Walk through the changelog with the client** at the next
   quarterly review (or out-of-band session for priority rollouts).
   What's new, what new findings to expect, what (if anything) the
   client needs to do before the upgrade.
3. **Client pulls the new tag** and re-runs `docker compose build`
   and `aletheia self-test`. The runbook in `README_HETARIOS.md`
   covers this step. Self-test verification is the consultant's
   contract that the new version is operational.
4. **Client runs `aletheia kb-load`** to refresh the in-database
   methodology snapshot to the new version.
5. **Client re-runs active diagnostics** under the new methodology.
   New findings (if any) flow into the engagement workspace's
   `findings_status.md` for triage at the next review.
6. **Update the deployment record** (`deployments/<engagement_code>.yaml`)
   with the new `methodology_version` and update
   `last_self_test_verified` to the date the new version's
   self-test was confirmed.
7. **Record in engagement workspace.** Add an entry to the
   workspace's `methodology_evolution_notes.md` documenting:
   - The version transition (from / to)
   - Date executed
   - New findings (if any) and their initial triage
   - Any client questions or methodology-evolution feedback the
     client provided

## Phase 4: Practice-side learnings

After all clients are rolled out (or a deferral window has passed):

1. **Aggregate methodology evolution feedback** from each
   engagement's `methodology_evolution_notes.md`. Look for patterns
   across engagements that suggest the next methodology version
   should address a recurring gap.
2. **Update the deferred-research-dimension status** if a
   methodology learning has triggered a deferral activation
   (e.g. HDQIF dimensions, calibration, fairness/bias).
3. **Promote overlay candidates.** Per `overlay_registry.md`, an
   overlay flagged as "promotion candidacy: target version v0.X.Y"
   should be promoted into the shipped methodology in v0.X.Y. Once
   promoted, remove the overlay entry (or mark it superseded).

## Failure modes and recovery

- **Self-test fails after upgrade.** The client's environment has
  drifted (config schema mismatch, missing API key, KB load
  failure). Rollback by checking out the previous tag. Investigate
  via `Troubleshooting` section in `README_HETARIOS.md`.
- **New findings are too disruptive.** If the new methodology
  version surfaces enough new findings that the client needs more
  than the next quarterly review to triage, schedule an additional
  out-of-band session and update the engagement's cadence
  temporarily.
- **Overlay re-validation fails.** The overlay's invariants no
  longer compose cleanly with the new methodology (ID collision,
  reference resolution failure, semantic conflict). Block the
  rollout for this client; revise the overlay; re-validate; then
  proceed.

## Cadence and timing

Methodology version bumps SHOULD ship no more frequently than
quarterly. Rapid methodology churn imposes operational load on
clients and undermines the consultant's reliability narrative. If
methodology learnings accumulate faster than quarterly, batch them
into a single version bump.

Exceptions: regulatory developments that change a methodology
grounding (e.g. a new FDA guidance that supersedes a current REF-)
may require an out-of-cycle version bump. Document the exception in
the changelog entry.
