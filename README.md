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
operational discipline of running consulting engagements at scale,
plus a small operator CLI (`aletheia-cp`) that validates
cross-references, scaffolds new engagements, and renders status views.

The records are deliberately low-fidelity (no database, no web
dashboard, no API, no fleet aggregation) because:

1. **Reality drives capability.** Building elaborate control-plane
   software before the first paying engagement risks baking in wrong
   assumptions about what consultants and clients actually need.
2. **Discipline transfers across consultants.** A second consultant
   joining the practice should be able to read this repo and
   understand how engagements are run.
3. **Records are evidence.** When a client asks "what did we decide
   in last quarter's review?", the answer is in the engagement
   workspace, not in someone's memory.

The CLI exists for one reason: the records have cross-references
between them (deployment record ↔ workspace mirror, methodology
version ↔ changelog, overlay ID ↔ overlay registry) and these
invariants should be machine-checkable rather than maintained by
hand-discipline. Same engineering posture as the engine repo: tests
catch drift before it spreads.

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
├── pyproject.toml                     # operator CLI package config
├── .pre-commit-config.yaml            # validate-on-commit hook
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
├── procedures/                        # consultant-facing how-to documents
│   ├── new_engagement_procedure.md
│   ├── methodology_update_procedure.md
│   ├── quarterly_review_procedure.md
│   └── deployment_change_procedure.md
├── src/aletheia_control_plane/        # operator CLI source
│   ├── cli.py                         # `aletheia-cp` click entry point
│   ├── schema.py                      # pydantic schema for deployment records
│   ├── validate.py                    # cross-reference validator
│   ├── scaffolding.py                 # new-engagement template copier
│   ├── registry.py                    # registry table renderer
│   ├── methodology_status.py          # methodology version status check
│   ├── review_prep.py                 # quarterly review prep scaffolder
│   └── paths.py                       # control plane root resolution
└── tests/                             # pytest suite (100% coverage gate)
```

---

## Operator CLI (`aletheia-cp`)

Install the package in editable mode:

```bash
pip install -e .[dev]
```

The CLI is invoked as `aletheia-cp` and walks up from the current
directory to find the control plane root, or accepts an explicit
`--root` path.

### Subcommands

```
aletheia-cp validate                    # validate every deployment + workspace
aletheia-cp validate <engagement_code>  # validate one engagement
aletheia-cp new <engagement_code>       # scaffold a new engagement
aletheia-cp registry                    # table of all engagements
aletheia-cp registry --phase active     # filter by phase (repeatable)
aletheia-cp methodology-status          # version status + stale engagements
aletheia-cp prep-review <engagement>    # scaffold a quarterly review prep file
```

### What `validate` checks

- Every deployment record under `deployments/` parses against the
  pydantic schema (engagement code format, system_id format, semver
  versions, jurisdiction enum, trust domain enum, contact email)
- Cross-field invariants (workspace_path matches engagement_code,
  last_interaction_date ≥ deployment_date, last_self_test_verified
  ≥ deployment_date, no duplicate jurisdictions or trust domains)
- Filename matches engagement_code (`deployments/X.yaml` has
  `engagement_code: X`)
- Engagement code uniqueness across all deployments
- `methodology_version` resolves to a real entry in
  `methodology_releases/changelog.md`
- `overlay_id`, if set, resolves to a real entry in
  `methodology_releases/overlay_registry.md`
- Every deployment has a corresponding workspace directory
- The workspace's `deployment_record.yaml` mirror matches the
  canonical deployment record byte-for-byte
- Every workspace directory has a corresponding deployment record

### Pre-commit hook

Install once: `pre-commit install`

Subsequent commits that touch `deployments/`, `engagement_workspaces/`,
or `methodology_releases/` will run `aletheia-cp validate` and reject
the commit on any error.

### Test suite

```bash
pytest                                  # run tests
pytest --cov=aletheia_control_plane     # with coverage
```

100% coverage is enforced via `fail_under = 100` in pyproject.toml.
The CLI mirrors the engine repo's engineering posture: drift between
records is caught by tests, not by hand-discipline.

---

## Aletheia version alignment

Templates target **Aletheia v0.5.0** (methodology) / **Hetarios
v0.5.0** (deployment chassis). When the engine bumps minor versions,
this repo's templates and procedures should be re-aligned in step.

The `methodology_releases/changelog.md` file is the load-bearing
record of which methodology version is shipped at any given time and
which clients are on which version.

The operator CLI versions independently from the engine. Its only
dependency on the engine is read-only: it parses
`methodology_releases/changelog.md` to verify that every deployment's
`methodology_version` field references a known release. It does not
import any engine code.

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

- The honest answer: structured markdown plus YAML records, plus a
  small operator CLI (`aletheia-cp`) that validates the
  cross-references between records on every commit. Same engineering
  posture as the engine — drift is caught by machine, not by
  hand-discipline. No SaaS platform, no fleet dashboard, no
  client-facing infrastructure.

The control plane is not the headline of trip conversations. It is
the answer to "but what about the operational mechanics?" — visible
when asked, not pushed unprompted.
