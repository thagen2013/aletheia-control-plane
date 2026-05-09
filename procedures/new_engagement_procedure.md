# New Engagement Procedure

The consultant-facing checklist for standing up a new paying
engagement. From "client signed" to "first quarterly review
scheduled."

This procedure ensures every engagement has consistent
record-keeping, a clean deployment, and a clear handoff into the
ongoing relationship.

---

## Phase 0: Pre-contract

(Before the contract is signed. Outside this procedure's scope, but
flagged so it's not lost.)

- Discovery conversation completed and documented in proposal
- Pricing calibrated and accepted
- Mutual NDA signed
- Engagement code chosen (lowercase, underscores, year-suffix
  recommended; e.g. `acme_h2_2026`)
- Engagement contract signed

When all of the above are done, proceed.

## Phase 1: Workspace creation (Day 1)

1. **Choose engagement code.** Final lowercase identifier.
2. **Create deployment record.** Copy
   `deployments/_template_deployment.yaml` to
   `deployments/<engagement_code>.yaml`. Fill in fields. Set
   `phase: discovery` initially.
3. **Create engagement workspace.** Copy
   `engagement_workspaces/_template/` to
   `engagement_workspaces/<engagement_code>/`.
4. **Fill engagement_overview.md.** Client name, contacts, scope,
   contract terms. This is the persistent context.
5. **Mirror deployment record.** Copy fields from
   `deployments/<engagement_code>.yaml` into
   `engagement_workspaces/<engagement_code>/deployment_record.yaml`.
   Both files in same commit going forward.
6. **Initialize the working files.**
   - `findings_status.md` — empty tables
   - `methodology_evolution_notes.md` — empty
   - `action_items.md` — empty open-items table
   - `communications_log.md` — first entry: "Engagement initiated,
     contract signed"
7. **Commit.** Single commit with message "Onboard engagement
   <engagement_code>".

## Phase 2: Deliverable bundle scaffold (Day 2)

1. **In `aletheia-deliverables/` repo, create
   `examples/<engagement_code>/`** by copying the templates from
   `aletheia-deliverables/templates/`.
2. **Fill the engagement README** in the new bundle directory with
   client-specific anonymization decisions, effort estimate basis,
   pricing approach, attribution discipline, methodology
   consistency note, and out-of-scope note. Use the existing
   `examples/rs1_imaging_ai_oem/README.md` as the structural
   reference.
3. **Commit.** Bundle scaffold ready to receive engagement-specific
   content as findings emerge.

## Phase 3: Hetarios deployment (Days 3-7)

The client deploys Hetarios per `aletheia-trust-engine/README_HETARIOS.md`.
The consultant supports.

1. **Configuration walkthrough** with client engineering team. Walk
   them through `hetarios.config.example.yaml` and help them fill
   their `hetarios.config.yaml`.
2. **B21 classification** for any China-origin artifacts. Help the
   client decide on `country_of_origin` and `data_classification_cn`
   per artifact category.
3. **Initial corpus indexing.** The client runs
   `aletheia index <corpus>` against their engagement corpus.
4. **Self-test verification.** Confirm `aletheia self-test` passes
   in the client environment. Update
   `deployments/<engagement_code>.yaml` field
   `last_self_test_verified: <YYYY-MM-DD>`.
5. **Phase transition.** Update
   `deployments/<engagement_code>.yaml` field `phase: onboarding`
   and `deployment_date: <YYYY-MM-DD>`. Update both the canonical
   record and the workspace mirror.

## Phase 4: Initial diagnostic (Weeks 2-3)

The client runs the initial diagnostic. The consultant reviews and
prepares the deliverable bundle.

1. **Client runs `aletheia diagnose`** for each in-scope trust
   domain.
2. **Client shares diagnostic output** with the consultant per
   their secure-sharing channel.
3. **Consultant copies agent reports verbatim** into
   `aletheia-deliverables/examples/<engagement_code>/05_agent_run_artifacts/`.
   Byte-equality is the contract; do not edit.
4. **Consultant fills `findings_status.md`** in the engagement
   workspace with all agent-traced findings, status `open`, and
   initial-status date.
5. **Consultant fills the deliverable bundle's
   `02_detailed_findings_report.md`** with the consolidated
   consultant-layer interpretation.
6. **Consultant fills `03_remediation_roadmap.md`,
   `04_methodology_and_scope.md`, `01_executive_briefing.md`** in
   sequence.
7. **Consultant adds any consultant-layer findings (C1, C2, …)**
   to both `findings_status.md` and
   `02_detailed_findings_report.md` with explicit attribution.
8. **Consultant fills `06_followup_proposal.md`** with the proposed
   Phase 2 scope based on findings.

## Phase 5: Initial handover (Week 4-8 depending on engagement size)

1. **Bundle review session** with the client. Walk through the
   deliverable bundle. Capture client questions and feedback.
2. **Update `communications_log.md`** with the bundle review
   session entry.
3. **Capture any methodology-evolution feedback** that emerged in
   the review session into `methodology_evolution_notes.md`.
4. **Phase transition.** Update
   `deployments/<engagement_code>.yaml` field `phase: active`.
5. **Schedule first quarterly review** per the agreed cadence.
   Place a calendar holdback. Commit a placeholder entry in the
   workspace.

## Phase 6: Transition to ongoing

The engagement is now in `active` phase. Subsequent operational
work follows:

- `quarterly_review_procedure.md` for each scheduled review
- `methodology_update_procedure.md` when methodology versions bump
- `deployment_change_procedure.md` for any client-requested config
  or deployment changes

---

## Failure modes and recovery

- **Engagement code collision.** Two engagements end up with the
  same engagement code. Catch at Phase 1 step 1 by checking the
  deployments/ directory for an existing file. Resolve by making
  the engagement code more specific (add quarter, add region).
- **Self-test fails at Phase 3 step 4.** Investigate per
  `README_HETARIOS.md` Troubleshooting. Do NOT advance
  `phase: onboarding` until self-test passes. The deployment is
  not real until self-test passes.
- **Initial diagnostic produces zero findings.** Verify the indexer
  classified artifacts correctly (`aletheia artifacts list`). If
  most artifacts are `type=other`, the classifier didn't
  recognize them — provide an `artifact-type-map` and re-index. A
  zero-finding result on a real corpus almost always means the
  indexer didn't see the corpus correctly, not that the corpus is
  perfect.
- **Client objects to a finding's framing.** Mark the finding
  `disputed` in `findings_status.md`, document the disagreement in
  `communications_log.md`, and resolve via discussion. The agent's
  finding is byte-stable and reproducible; the consultant-layer
  framing can be revised if the client has substantive context the
  consultant did not have.
