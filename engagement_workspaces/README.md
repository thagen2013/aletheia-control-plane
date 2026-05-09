# Engagement Workspaces

One folder per active engagement. Captures everything about a
specific client engagement that does NOT belong in the deployment
registry, the methodology releases, or the deliverable bundle.

The workspace is the consultant's primary working surface for an
active engagement. Quarterly reviews are prepared from the
workspace; action items are tracked in the workspace; methodology
evolution feedback is collected in the workspace.

## Structure

```
engagement_workspaces/
├── README.md                                  # this file
├── _template/                                 # blank workspace, copied per engagement
│   ├── engagement_overview.md
│   ├── deployment_record.yaml
│   ├── quarterly_review_prep_template.md
│   ├── findings_status.md
│   ├── methodology_evolution_notes.md
│   ├── action_items.md
│   └── communications_log.md
└── <engagement_code>/                         # per-client workspace
    └── (same shape as _template)
```

## Files in each workspace

### `engagement_overview.md`

The persistent context document for the engagement: client name,
contacts, scope, contract terms, retainer status, key dates,
significant history. Updated when context changes; not a working
document.

### `deployment_record.yaml`

Engagement-specific deployment metadata. Mirrors the canonical
record in `deployments/<engagement_code>.yaml` but lives also in
the workspace for self-contained reading. Update both files in the
same commit when deployment changes occur.

### `quarterly_review_prep_template.md`

Template for preparing a quarterly review. Each quarterly review
session creates a new file like `quarterly_review_2026Q1.md` from
this template. The template covers: agenda, finding status changes
since last review, methodology updates since last review, action
item follow-up, new findings, methodology evolution discussion,
forward-looking action items.

### `findings_status.md`

Living spreadsheet-style record of all findings across the
engagement: agent-traced findings (F1, F2, …) and consultant-layer
findings (C1, C2, …). Status transitions over time
(open → in-remediation → resolved → verified). Cross-references to
the deliverable bundle's detailed findings report.

### `methodology_evolution_notes.md`

Notes about how the engagement is informing methodology evolution.
Patterns the consultant notices, gaps the methodology surfaces in
this client's corpus, suggestions for future invariants or failure
modes. This is the feedback channel from engagement-reality to
shipped methodology.

### `action_items.md`

Specific tracked action items: who owes what to whom by when.
Lightweight; not a project management tool. Items roll forward
quarterly. Closed items remain in the file as a closed-item
section so the history is preserved.

### `communications_log.md`

Brief log of substantive consultant-client communications:
methodology questions, deployment incidents, scope conversations,
escalations. Not every email; just the substantive interactions
that affect engagement direction.

## Workflow

When a paying engagement starts:

1. Copy `_template/` to `<engagement_code>/`
2. Fill in `engagement_overview.md` and `deployment_record.yaml`
3. As findings emerge from the initial diagnostic, populate
   `findings_status.md`
4. As work progresses, append to `action_items.md` and
   `communications_log.md`
5. Before each quarterly review, copy
   `quarterly_review_prep_template.md` to
   `quarterly_review_<YYYY><Q#>.md` and prepare the review

## Privacy

Workspaces contain client-confidential information. Do not commit
to public repos. Access is granted to consultants on the engagement
team and to no one else.
