# Methodology Update Procedure

How a methodology version bump propagates from the engine repo to
active client deployments.

This procedure references and complements
`methodology_releases/release_procedure.md`. The release procedure
is from the methodology's perspective (the version being released);
this procedure is from a single engagement's perspective (a specific
client absorbing a methodology update).

When a methodology version bumps, both procedures are followed: the
release procedure once for the version (Phase 1, Phase 4), and this
procedure once per active engagement (replacing the per-client
sections of the release procedure for that specific engagement).

---

## Trigger

A new methodology version has been released and is now sitting at a
git tag in the engine repo. The release procedure's Phase 1 has
been completed. Each active engagement now needs to be evaluated
and (typically) rolled forward.

## Step 1: Read the changelog

Open `methodology_releases/changelog.md` and read the entry for
the new version. Specifically note:

- **What's new** — new invariants, failure modes, references,
  semantic revisions
- **Engagement implications** — which corpus shapes are affected
- **Open methodology gaps** — what's NOT in the new version that
  the client may still ask about
- **Migration notes** — anything the client needs to do during
  upgrade

## Step 2: Per-engagement evaluation

For each engagement workspace, evaluate three questions:

### Q1: Is this engagement in a state to receive an update?

Check `deployments/<engagement_code>.yaml` field `phase`:

- `discovery` — no deployment exists; nothing to update
- `onboarding` — first diagnostic in flight; deferring update may
  be appropriate to avoid scope creep
- `active` — typical case, update at next quarterly review
- `transitioning` — engagement is winding down or expanding;
  evaluate whether update lands during the transition or is
  deferred until the new state is established
- `closed` — no longer active; no update

### Q2: Is the methodology delta material to this engagement's corpus?

Read the changelog's "engagement implications" section against the
client's corpus shape (in
`engagement_workspaces/<engagement_code>/engagement_overview.md`,
field `system type` and `trust domains in scope`).

If the version bump only adds invariants for trust domains the
client doesn't have in scope, the update is non-material. Roll
forward routinely with no disruption to the client.

If the version bump adds invariants/failure modes likely to fire on
this client's corpus, the update is material. The client should
know what to expect.

### Q3: Is there a sensitivity reason to defer?

Check the engagement's recent activity in `communications_log.md`
and the upcoming-events section in `quarterly_review_prep_template.md`
or whatever working file currently tracks pending events:

- Mid-submission to FDA / NMPA
- Mid-audit by regulator or notified body
- Active CAPA or Form 483 response
- Major personnel transition

Sensitivity periods are a reason to defer the update by one
quarterly review cycle. Document the deferral in the engagement
workspace's `methodology_evolution_notes.md`.

## Step 3: Schedule the update

Three options based on Step 2 evaluation:

### Option A: Quarterly window (default)

The update lands during the next scheduled quarterly review. The
review's prep document includes the changelog walkthrough. The
client confirms the upgrade during the review session.

Use this option when: engagement is in `active` phase, methodology
delta is non-material or modestly material, no sensitivity period
applies.

### Option B: Out-of-band priority

The update lands ahead of the next quarterly review because the
methodology version addresses something the client needs to know
about now (e.g. a new regulatory development).

Use this option when: methodology delta is highly material AND the
material is regulatory-development-driven AND the client benefits
from early awareness.

Procedure for out-of-band updates:

1. Email or call the client lead describing what's in the new
   methodology version and why it matters now
2. Schedule an out-of-band session (30-60 minutes) to walk through
   the changelog and plan the upgrade
3. Execute the upgrade per Step 4 below
4. Document the out-of-band session in `communications_log.md`

### Option C: Defer

The update does not land at this engagement until a future date.
Reasons to defer were established in Step 2.

Document the deferral in
`engagement_workspaces/<engagement_code>/methodology_evolution_notes.md`
with the reason and the planned future date for re-evaluation.

The deployment record stays on the previous methodology version
until the deferral is lifted.

## Step 4: Execute the upgrade

Whether Option A or Option B, the actual upgrade procedure is the
same. Reference: `methodology_releases/release_procedure.md` Phase
3 covers this. Briefly:

1. Client pulls the new git tag, runs `docker compose build`
2. Client runs `aletheia self-test` and confirms it passes
3. Client runs `aletheia kb-load` to refresh the database
4. Client re-runs active diagnostics under the new methodology
5. Update `deployments/<engagement_code>.yaml` and the workspace
   mirror with new `methodology_version` and updated
   `last_self_test_verified`
6. Update `engagement_workspaces/<engagement_code>/findings_status.md`
   with any new findings emitted under the new methodology
7. Add an entry to
   `engagement_workspaces/<engagement_code>/methodology_evolution_notes.md`
   describing the version transition, date, new findings, and
   client feedback

## Step 5: Capture learnings

After all engagements have absorbed (or formally deferred) the new
version, contribute to release procedure Phase 4 (practice-side
learnings):

- Aggregate methodology-evolution feedback across engagements
- Note patterns: did multiple clients react similarly to a
  specific change?
- Identify candidates for the next methodology version

---

## Failure modes and recovery

- **Client environment self-test fails after upgrade.** Roll back
  by checking out the previous tag. Record the failure in the
  engagement's `communications_log.md`. Investigate per
  `README_HETARIOS.md` Troubleshooting. Common causes: API key
  drift, KB schema mismatch (rare; would have been caught in
  release procedure Phase 1), filesystem permissions on the
  mounted data volume.
- **New findings overwhelm client team's bandwidth.** Schedule an
  additional working session beyond the normal quarterly cadence.
  Triage findings into "must-address" and "can-defer" tiers. Update
  `findings_status.md` accordingly.
- **Overlay incompatible with new methodology.** Reference
  `methodology_releases/overlay_registry.md` re-validation
  procedure. Block the upgrade for this client until overlay is
  revised.
- **Methodology-evolution feedback contradicts another engagement's
  feedback.** Both feedback items are valid observations. Record
  both in respective `methodology_evolution_notes.md` files. The
  next methodology version may need to navigate the tension
  explicitly rather than picking one direction silently.
