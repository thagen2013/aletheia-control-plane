# Findings Status — [ENGAGEMENT CODE]

Living record of all findings across the engagement. Update as
findings are remediated or as new findings emerge from subsequent
diagnostic runs.

The deliverable bundle's `02_detailed_findings_report.md` is the
formal handover record at engagement-close. This file is the
working record of finding lifecycle through the engagement.

---

## Status taxonomy

| Status | Meaning |
|---|---|
| `open` | Finding is active; remediation not yet started |
| `in_remediation` | Client team is actively working on the fix |
| `pending_verification` | Client says fixed; consultant has not yet verified |
| `resolved` | Verified by consultant via re-run of Aletheia or document review |
| `verified` | Resolved AND held through at least one subsequent quarterly review |
| `deferred` | Acknowledged by client but deferred to a later phase by mutual agreement |
| `disputed` | Client disagrees the finding is valid; under discussion |

---

## Agent-traced findings

These are the findings emitted directly by Aletheia. Each row is
one finding from the engagement's deliverable bundle's detailed
findings report.

| ID | Aletheia ID | Trust domain | Invariant(s) | Severity | Initial status (date) | Current status (date) | Notes |
|---|---|---|---|---|---|---|---|
| F1 | | | | | open ([YYYY-MM-DD]) | | |
| F2 | | | | | | | |
| F3 | | | | | | | |
| F4 | | | | | | | |
| F5 | | | | | | | |

---

## Consultant-layer findings

Findings that the consultant produced from QMS / regulatory /
process review beyond Aletheia's current methodology coverage.

| ID | Description | Severity | Initial status (date) | Current status (date) | Notes |
|---|---|---|---|---|---|
| C1 | | | | | |

---

## Status transitions log

Append entries when status changes. Date, finding ID, transition,
brief reason. Do not delete prior entries — the transition history
is the audit trail.

- **[YYYY-MM-DD]** F1: open → in_remediation. [Brief reason or
  trigger.]
- **[YYYY-MM-DD]** F2: in_remediation → pending_verification.
  [Notes.]

---

## Re-run record

When the consultant re-runs Aletheia on an updated corpus to verify
finding resolution, record the run here.

| Run date | Aletheia version | Findings emitted | Status verifications confirmed | Notes |
|---|---|---|---|---|
| [YYYY-MM-DD] | v0.5.0 | [F#, F#, ...] | [F# verified resolved, ...] | |

---

## New-findings emergence record

When subsequent diagnostic runs (on updated corpora or under updated
methodology) emit findings that were not in the initial engagement,
record them here.

| First-emerged date | Aletheia version | Finding | Initial assessment |
|---|---|---|---|
| [YYYY-MM-DD] | | | |
