# Deployment Change Procedure

How a change to a client's Hetarios deployment configuration is
evaluated, executed, and recorded.

This procedure covers changes to the deployment that are NOT
methodology version bumps (those follow
`methodology_update_procedure.md`). Examples of changes covered
here:

- Trust domain added to the engagement
- Jurisdiction added (e.g. client expands from FDA-only to FDA + CE)
- Backend change (deterministic → llm or vice versa)
- B21 default policy change
- Cadence change
- Retainer tier change
- Contact change

---

## Trigger

A change request originates from one of three sources:

1. **Client request** — the client emails or raises in a quarterly
   review that they want a change
2. **Consultant initiative** — the consultant proposes a change in a
   review session (e.g. "your engagement has matured enough that we
   could activate the data_quality domain")
3. **External trigger** — a regulatory development or methodology
   release suggests a change

In all cases, the change is documented before execution.

## Step 1: Document the request

Add an entry to the engagement workspace's
`communications_log.md`:

- Date
- Source (client / consultant / external)
- Change requested
- Reason

If the change is consultant-initiated, also add an entry to
`action_items.md` for the consultant to formalize the proposal to
the client.

## Step 2: Evaluate the change

Three considerations:

### Consideration 1: Scope and contract

Does the change fall within the existing engagement contract, or
does it require a contract amendment?

Examples:
- Adding a trust domain: typically requires a contract amendment
  (more scope = different fee)
- Cadence change: usually within existing contract
- Backend change (deterministic → llm): may have cost implications
  if the LLM API usage costs are passthrough; check contract
- Retainer tier change: requires contract amendment

If a contract amendment is needed, that is a separate workstream.
This procedure resumes after the amendment is signed.

### Consideration 2: Operational impact

Does the change affect the deployment's operational state?

- Trust domain added: client needs to re-run diagnostics under
  the new domain; new findings may emerge
- Jurisdiction added: methodology references for the new
  jurisdiction become relevant; existing findings may need
  re-mapping
- Backend changed to llm: requires API keys, increased per-run
  cost, different finding shape (LLM seam vs deterministic
  baseline)
- B21 default policy changed: re-classification of existing
  artifacts may be needed (the engine's PR-Q reclassification
  with history infrastructure handles this; reference
  `aletheia-trust-engine`)
- Cadence change: review prep cycle adjusts

Operational impact informs whether the change rolls out at the
next quarterly review or out-of-band.

### Consideration 3: Methodology compatibility

Does the change interact with current methodology coverage?

- Adding `data_quality` trust domain on a v0.5.0 deployment:
  supported, methodology has DQ coverage
- Adding a new jurisdiction not yet in shipped methodology
  references: may need an overlay (per
  `methodology_releases/overlay_registry.md`) or a methodology
  version bump
- Backend changed to llm: works in v0.5.0 but the agent's
  `_call_anthropic` is allow-listed but not gated through the
  transfer_gate; this is acceptable for English-language US-origin
  corpora but the consultant should evaluate whether the change is
  appropriate for China-origin or sensitive corpora

If methodology compatibility is a concern, document in
`methodology_evolution_notes.md` and resolve before executing the
change.

## Step 3: Schedule and execute

For most changes, the change is executed at the next quarterly
review or at an out-of-band session. The execution path depends on
what changed:

### For trust domain or jurisdiction additions

1. Update `hetarios.config.yaml` on the client side (the client
   makes the edit; the consultant reviews)
2. Restart the deployment (`docker compose down && docker compose
   up`)
3. Re-run `aletheia self-test` and confirm
4. Re-run diagnostics under the new scope
5. New findings flow into the engagement's `findings_status.md`
6. Update `deployments/<engagement_code>.yaml` and the workspace
   mirror to reflect the new scope

### For backend changes

1. Update `hetarios.config.yaml` field `backend.kind` (and
   `backend.model_id` if changing to llm)
2. Ensure API keys are present in the deployment environment if
   moving to llm
3. Restart the deployment
4. Re-run `aletheia self-test`
5. The next diagnostic run will use the new backend; the finding
   shape may differ from the baseline. Note the transition in the
   workspace's `methodology_evolution_notes.md`.

### For B21 default policy changes

1. Update `hetarios.config.yaml` `b21` defaults
2. Re-classify existing artifacts as needed (the engine supports
   this with reclassification-with-history per PR-Q)
3. Document the policy change rationale in
   `engagement_overview.md`

### For cadence or retainer tier changes

1. Update `deployments/<engagement_code>.yaml` and the workspace
   mirror
2. Update `engagement_overview.md` with the new contract terms
3. Adjust calendar holdbacks for review sessions per the new
   cadence
4. Communicate the change to client team if any workflow
   adjustments are required on their side

### For contact changes

1. Update `engagement_overview.md` and the deployment record's
   `primary_contact` field
2. Send a brief introduction email if a new primary contact is
   joining

## Step 4: Record the change

After execution:

1. **Commit the change** to deployment records and workspace mirror
   in a single commit. Commit message names the engagement and the
   change.
2. **Log it in `communications_log.md`** with date, change, and
   outcome.
3. **Update `findings_status.md`** if new findings were emitted
   under the changed scope.
4. **Note in `methodology_evolution_notes.md`** if the change
   surfaces methodology questions worth tracking.

---

## Failure modes and recovery

- **Self-test fails after configuration change.** Roll back the
  config change (revert `hetarios.config.yaml`). Investigate per
  `README_HETARIOS.md` Troubleshooting. The deployment is not real
  until self-test passes.
- **B21 reclassification produces unexpected refusals.** Some
  artifacts that were transmitted under the old policy now fall
  into a refused category under the new policy. This is the gate
  working as designed; review the affected artifacts and decide:
  formally reclassify them, document the limitation in the
  engagement workspace, or revisit the policy.
- **Backend change to llm produces dramatically different
  findings.** The deterministic baseline and the LLM seam can
  produce different finding shapes. This is expected — they are
  different agents. Update the deliverable bundle's
  `04_methodology_and_scope.md` to reflect that the LLM seam is
  in use, and explain to the client that the LLM-seam findings
  carry confidence scores while the deterministic-baseline findings
  do not.
- **Contract amendment delayed.** If a change requires contract
  amendment and the amendment process stalls, the deployment stays
  on the previous configuration until the amendment is signed.
  Document the pending amendment in `engagement_overview.md` so
  it is not lost.
