# aletheia-control-plane

Consultant-side operational records for engagements run on the
**Aletheia Trust Engine** under the **Hetarios** delivery model.

This repo is the third leg of the engagement model:

- **`aletheia-trust-engine/`** — methodology, agents, CLI, Hetarios
  deployment chassis. The thing the client deploys and operates.
- **`aletheia-deliverables/`** — engagement deliverable templates and
  worked examples (executive briefing, detailed findings, remediation
  roadmap, methodology and scope, agent run artifacts, follow-up
  proposal). The thing the consultant produces and hands over.
- **`aletheia-control-plane/`** (this repo) — the consultant's
  operational records: which deployment is at which client running
  which methodology version, what was discussed in the last quarterly
  review, what action items are open, what methodology evolution this
  engagement surfaced. The thing the consultant maintains.

The three repos together describe a complete engagement: the client
deploys the engine, the consultant produces the deliverable bundle
and maintains the engagement workspace, methodology evolution feeds
back into the engine over time.

---

## What this repo is

A structured set of markdown files and YAML records that capture the
operational discipline of running consulting engagements at scale.
The discipline matters more than the technology — the records are
deliberately low-fidelity (no database, no web dashboard, no API)
because:

1. **Reality drives capability.** Building elaborate control-plane
   software before the first paying engagement risks baking in wrong
   assumptions about what consultants and clients actually need.
2. **Discipline transfers across consultants.** A second consultant
   joining the practice should be able to read this repo and
   understand how engagements are run.
3. **Records are evidence.** When a client asks "what did we decide
   in last quarter's review?", the answer is in the engagement
   workspace, not in someone's memory.

## What this repo is NOT

- **Not a SaaS product.** No customers see this directly.
- **Not multi-tenant infrastructure.** One folder per client; no
  shared aggregation logic.
- **Not a fleet dashboard.** When the practice has 3+ active
  engagements, a small fleet view will be added — but not before.
- **Not a sync/comms layer.** Methodology updates flow through git
  and the engine repo; client communication flows through the
  consultant's normal channels.
- **Not the engine.** Methodology lives in the engine repo; this
  repo only references methodology versions, never embeds them.

---

## Structure

```
aletheia-control-plane/
├── README.md                          # this file
├── deployments/                       # one record per client deployment
│   ├── README.md
│   ├── _template_deployment.yaml
│   └── (per-client deployment files)
├── methodology_releases/              # consultant-side release ops
│   ├── README.md
│   ├── changelog.md                   # methodology version history
│   ├── overlay_registry.md            # client-specific KB overlays
│   └── release_procedure.md           # how a methodology version ships
├── engagement_workspaces/             # one workspace per active engagement
│   ├── README.md
│   ├── _template/                     # blank workspace, copied per engagement
│   │   ├── engagement_overview.md
│   │   ├── deployment_record.yaml
│   │   ├── quarterly_review_prep_template.md
│   │   ├── findings_status.md
│   │   ├── methodology_evolution_notes.md
│   │   ├── action_items.md
│   │   └── communications_log.md
│   └── (per-client workspaces created at engagement start)
└── procedures/                        # consultant-facing how-to documents
    ├── new_engagement_procedure.md
    ├── methodology_update_procedure.md
    ├── quarterly_review_procedure.md
    └── deployment_change_procedure.md
```

---

## Aletheia version alignment

Templates target **Aletheia v0.5.0** (methodology) / **Hetarios
v0.5.0** (deployment chassis). When the engine bumps minor versions,
this repo's templates and procedures should be re-aligned in step.

The `methodology_releases/changelog.md` file is the load-bearing
record of which methodology version is shipped at any given time and
which clients are on which version.

---

## Privacy and confidentiality

Per-client deployment records and engagement workspaces contain
client-confidential information:

- system identifiers
- deployment dates and configurations
- finding summaries
- engagement notes
- pricing and retainer status

These records are NOT to be committed to a public-facing repository.
The intended deployment is a private repo accessible only to the
consultant practice. When a consultant onboards or offboards, this
repo's access is granted or revoked accordingly.

The `_template_*` files and `_template/` workspace are
consultant-side discipline; they contain no client information and
can be shared between consultants joining the practice.

---

## How this relates to trip conversations

When a prospect asks "how do you stay engaged after deployment?":

- Open `engagement_workspaces/_template/` and walk through the
  structure
- Show `quarterly_review_prep_template.md` to demonstrate the
  cadence discipline
- Reference `procedures/quarterly_review_procedure.md` to show the
  named consultant procedure

When a prospect asks "how do you handle methodology updates?":

- Reference `procedures/methodology_update_procedure.md`
- Show `methodology_releases/changelog.md` (initially empty or
  with v0.5.0 entry only)
- Explain the deployment-registry update flow

When a prospect asks "how do you keep track of all this?":

- The honest answer is: this repo, plus the deliverable bundle,
  plus normal communication channels. Not a custom platform — the
  discipline is in the structured records, not in elaborate
  software.

The control plane is not the headline of trip conversations. It is
the answer to "but what about the operational mechanics?" — visible
when asked, not pushed unprompted.
