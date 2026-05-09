# Methodology Changelog

Consultant-side narrative of methodology evolution. The
machine-readable methodology lives in the engine repo at
`knowledge_base/*_v0_X_Y.yaml`; this file is the operator-facing
narrative of what changed between versions and why it matters in
client engagements.

When a new methodology version ships, add an entry at the top.
Entries follow reverse chronological order (newest first).

---

## v0.5.0 (current shipped) — Days 61-70 Data Quality activation

**Released:** 2026 (Day 61-70 build window)
**Engine reference:** `aletheia-trust-engine/knowledge_base/*_v0_5_0.yaml`
**Counts:** 26 invariants, 29 failure modes, 73 references

### What's new

- **Data Quality trust domain activation.** Three new invariants
  added: INV-024 (fitness-for-purpose RWE), INV-025 (multi-source
  linkage quality), INV-026 (distributed-data-network harmonization).
- **Three new failure modes.** FM-027 (multi-source RWE claim
  without fitness assessment), FM-028 (linkage quality not disclosed),
  FM-029 (distributed-network harmonization not documented).
- **Two new methodology references.** REF-SENTINEL-DQ (FDA Sentinel
  data-quality check levels), REF-CPA-GUIDE (Chinese Pharmacoepidemiology
  Association guide).
- **Bi-jurisdictional grounding.** DQ invariants are grounded in
  both US (FDA RWE Framework, Sentinel) and China (CPA Guide)
  references.

### Engagement implications

- Engagements with RWE / data-platform corpora can now invoke the
  `data_quality` trust domain. Pre-v0.5.0 deployments asking for
  DQ coverage need to upgrade.
- `audit_trail` and `model_validation` domains are unchanged from
  v0.4.0; clients on those domains only do not require immediate
  upgrade.

### Open methodology gaps

- HDQIF-dimension-specific coverage (accessibility, interoperability,
  metadata verification, promptness, traceability of origin,
  scarcity/rarity) is not yet activated as a coverage axis. Trigger:
  first Chinese RWE engagement that surfaces a specific HDQIF
  dimension as engagement-relevant.
- Calibration and fairness/bias are deferred research dimensions.
  See `aletheia-trust-engine/docs/v0_1_2_named_deferrals.md`.

### Migration notes

- Pre-v0.5.0 deployments upgrade by pulling the new git tag and
  running `aletheia kb-load`. The SQLite database absorbs additive
  schema changes automatically; no client-side data migration
  required.
- Re-running existing diagnostics on v0.5.0 may produce additional
  findings if the corpus contains DQ-relevant content. The new
  finding count should be communicated to the client at the next
  quarterly review.

---

## Earlier versions

Earlier versions (v0.1.2 through v0.4.0) shipped during the
methodology-development phase before the first engagement-ready
release. Their detailed changelogs live in the engine repo's commit
history. Pre-v0.5.0 deployments should be treated as
development-tier and upgraded to v0.5.0 before any paying engagement.

---

## How to add a new entry

When the engine ships a new methodology version:

1. Add a new section at the top of this file with the version
   number and release date.
2. Document what's new (new invariants, failure modes, references,
   semantic revisions).
3. Document engagement implications (which client engagements are
   affected, whether immediate upgrade is required).
4. Document open methodology gaps known at release time.
5. Document migration notes (if any).
6. Update each client's deployment record (`deployments/<engagement_code>.yaml`)
   to reflect the new version once they upgrade.
7. Reference this entry from any engagement workspace's
   `methodology_evolution_notes.md` if the version bump surfaces
   client-specific implications.
