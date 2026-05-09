# Methodology Evolution Notes — [ENGAGEMENT CODE]

The feedback channel from this engagement to shipped methodology.
Notes about patterns the consultant notices, gaps the methodology
surfaces in this client's corpus, and suggestions for future
invariants, failure modes, or grounding references.

This is the engagement-side artifact that closes the methodology
evolution loop. Items captured here may eventually feed into
methodology version bumps in the engine repo.

---

## How to use this file

When the consultant notices any of the following, add an entry:

- A pattern across multiple findings in this engagement that
  suggests a missing invariant
- A regulatory grounding the methodology should cite that it
  currently does not
- A failure mode the agent did not surface but the consultant
  caught from corpus review
- A discipline the client requested that should be (or should not
  be) absorbed into shipped methodology
- A language-coverage gap the methodology limits framework
  surfaced
- A trust-domain extension the engagement is pulling for

Entries are dated; append, do not rewrite. Entries get a status
that tracks their journey from observation to (potential)
methodology promotion.

---

## Status taxonomy for evolution notes

| Status | Meaning |
|---|---|
| `observed` | Pattern noticed; not yet evaluated for promotion |
| `under_consideration` | Being weighed against other methodology priorities |
| `proposed_for_v0_X_Y` | Concrete proposal for a specific future version |
| `promoted` | Landed in shipped methodology; entry kept for history |
| `declined` | Decided not to promote; reason recorded |
| `overlay_candidate` | Being held as a client-specific overlay rather than shipped methodology |

---

## Active evolution notes

(Initial state: empty)

When entries are added, follow the template:

```
### EN-001 — [Brief descriptive title]

- **Observed:** [YYYY-MM-DD]
- **Trust domain (if any):** [audit_trail / model_validation /
  data_quality / cross-domain]
- **Status:** [observed / under_consideration / ...]
- **Description:**
  Two-paragraph description of what was observed in the engagement
  and what methodology gap or extension it suggests.
- **Engagement context:**
  Which findings in this engagement triggered the observation.
  Reference finding IDs from `findings_status.md`.
- **Cross-engagement signal:**
  Has this pattern been observed in other engagements? Reference
  other engagement workspaces if applicable.
- **Proposed action:**
  Concrete proposal — new invariant draft, new failure mode draft,
  new grounding reference, semantic revision target. Or a
  recommendation to leave as-is if the gap does not justify
  promotion.
- **Last updated:** [YYYY-MM-DD]
```

---

## Promoted to shipped methodology

(History of evolution notes that landed in shipped methodology.
Useful for tracing methodology lineage to engagement reality.)

---

## Declined for promotion

(History of evolution notes that were considered but not promoted,
with reasons. Useful so future consultants don't re-litigate
already-decided-against proposals.)

---

## Cross-references

- Engine methodology source: `aletheia-trust-engine/knowledge_base/`
- Methodology changelog: `../../methodology_releases/changelog.md`
- Overlay registry: `../../methodology_releases/overlay_registry.md`
- Deferred research dimensions: `aletheia-trust-engine/docs/v0_1_2_named_deferrals.md`
