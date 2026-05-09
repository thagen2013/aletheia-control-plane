# Quarterly Review Procedure

How a quarterly review session is prepared, executed, and closed.

The quarterly review is the load-bearing engagement ritual. It is
where consultant judgment value lives: interpretation of agent
findings, prioritization, methodology evolution discussion,
forward-looking planning. The Hetarios deployment runs continuously
between reviews; the consultant's concentrated attention happens at
the review.

This procedure ensures every review follows consistent discipline,
so a second consultant joining the practice can prepare and run a
review cleanly.

---

## Cadence

The default cadence is quarterly. The engagement's
`deployments/<engagement_code>.yaml` field `cadence` records the
agreed cadence; some engagements run weekly during active
remediation phases and shift to quarterly steady-state. Honor the
agreed cadence.

A quarterly review session typically runs 60-90 minutes. Out-of-band
sessions (per `methodology_update_procedure.md`) are typically
30-60 minutes.

---

## Phase 1: Preparation (consultant, ~2 hours, ideally a week before)

1. **Open the engagement workspace.**
   `engagement_workspaces/<engagement_code>/`
2. **Run the prep checklist** from
   `quarterly_review_prep_template.md`. Specifically:
   - Findings status is current
   - Action items from previous review have been checked
   - Methodology evolution notes have been reviewed
   - Engagement-specific Aletheia diagnostic has been re-run
     (this is where the agent's value compounds — re-running
     against the current corpus tells the consultant which findings
     have been resolved, which remain, and which are new)
   - Communications since last review have been read
   - Pricing / retainer status is current
   - If methodology version changed since last review, update has
     been executed per `methodology_update_procedure.md`
3. **Copy the prep template** to a session-specific file:
   `quarterly_review_<YYYY>Q<#>.md` in the workspace.
4. **Fill the prep document.**
   - Pull action item statuses from `action_items.md`
   - Pull finding status changes from `findings_status.md`
   - Note methodology updates if any
   - Note new findings from latest diagnostic run
   - Identify methodology-evolution patterns to discuss
   - Draft forward-looking action items
   - Note any sensitivities to watch
5. **Distill talking points.** The 3-5 things the client will hear
   from the consultant in the review. This is what opens the
   session.
6. **Send pre-read** (optional but recommended for senior
   stakeholders). A 1-page extract of talking points + finding
   status changes + new findings, sent 1-2 days before the review.

## Phase 2: Execution (consultant + client, 60-90 minutes)

Suggested agenda (from `quarterly_review_prep_template.md`):

1. **Status of action items from last review** (5 min) — what
   closed, what's still open, what's blocked
2. **Findings status update** (15 min) — what moved forward, what
   stalled, status transitions since last review
3. **Methodology updates since last review** (10 min, if
   applicable) — walk through the changelog entry
4. **New findings from latest diagnostic run** (15 min, if any) —
   what the agent surfaced since last review
5. **Methodology-evolution discussion** (10 min) — patterns the
   consultant has noticed, client feedback to capture
6. **Forward-looking action items and next-quarter focus** (15
   min) — what each side commits to before the next review
7. **Open questions / scope conversations** (open-ended) — pricing
   adjustments, expansion options, escalations

The agenda is a guide, not a script. Adjust based on what the
engagement actually needs. Some quarterly reviews are short
status-keepers; others are long working sessions on a specific
methodology question.

### Discipline during the review

- **Take notes during the session.** Capture decisions, action
  items, methodology-evolution feedback. The post-review fill-in
  is easier when notes are taken in real time.
- **Honor the agent-vs-consultant attribution discipline.** When
  discussing findings, be clear which are agent-traced and which
  are consultant-layer. The deliverable bundle's discipline carries
  through to the review conversation.
- **Don't over-promise on methodology evolution.** A client
  request for a new invariant is a signal, not a commitment. Note
  it in `methodology_evolution_notes.md` with status `observed`;
  evaluation against other priorities happens later.

## Phase 3: Closure (consultant, ~1 hour, within 2 days of the
session)

1. **Fill the post-review section** of the
   `quarterly_review_<YYYY>Q<#>.md` file.
2. **Move new action items** from the review notes into
   `action_items.md`.
3. **Move methodology-evolution feedback** from the review notes
   into `methodology_evolution_notes.md` with status `observed`.
4. **Add a communications log entry** to `communications_log.md`
   summarizing the review session.
5. **Update finding statuses** in `findings_status.md` if the
   review surfaced status changes.
6. **Update deployment record** if anything changed (cadence,
   retainer tier, contacts).
7. **Send the client a follow-up email or document** with: what was
   decided, action items per side with due dates, next review date.
   Brief; the formal record is in the workspace, the follow-up is
   the client-facing summary.
8. **Schedule the next review.** Calendar holdback at the agreed
   cadence (default: quarterly). Update the engagement workspace
   with the placeholder.

## Phase 4: Deliverable bundle update (as needed)

If the review produced changes that affect the deliverable bundle —
finding status transitions, methodology version updates, new
findings absorbed — update the corresponding sections of the
engagement's deliverable bundle in
`aletheia-deliverables/examples/<engagement_code>/`.

The deliverable bundle is the formal handover record; keep it
current with the engagement's actual state.

---

## Failure modes and recovery

- **Client cancels or no-shows the review.** Follow up promptly
  to reschedule. Two consecutive cancellations is a signal: the
  retainer relationship may be drifting. Address proactively rather
  than wait.
- **Review surfaces a finding the consultant missed.** Add it as a
  new consultant-layer finding (Cn) to `findings_status.md` and
  the deliverable bundle's `02_detailed_findings_report.md`. Note
  the lateness in `methodology_evolution_notes.md` — sometimes a
  late-surfacing finding indicates the methodology should have
  caught it.
- **Action items consistently slip.** Check
  `carry-forward log` in `action_items.md`. Three consecutive
  carry-forwards on the same item is a signal: either the action
  isn't really actionable, the owner is overloaded, or the priority
  has changed. Rescope or close as appropriate.
- **Client asks about findings the consultant hasn't reviewed.**
  Acknowledge, take note, follow up after the session. Don't
  improvise — accuracy of finding interpretation is part of the
  consulting value.
- **Review runs over time.** Better to schedule a follow-up
  session than to compress closing items. The forward-looking
  action items section is the most important; don't skip it
  because of clock pressure.

---

## When the cadence isn't quarterly

For weekly-cadence engagements (active remediation phase), the
"quarterly review" structure is too heavy. Use a lightweight
weekly-check structure:

- 30 minutes
- Action item status only
- Finding status changes only
- One forward-looking task per side per week

Weekly checks roll up into a "quarter" after ~12 weeks; at that
point, run a full quarterly review with the heavier agenda.

For biweekly or monthly engagements, scale the prep and session
length accordingly. The discipline of preparation, execution,
closure, and follow-up is the same.
