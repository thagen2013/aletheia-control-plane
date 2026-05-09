# Deployment Registry

Single-source-of-truth for every Hetarios deployment the consultant
practice is responsible for. One file per deployment.

This is the consultant's record of what is running where; the client
has their own deployment under their own operational control. This
registry exists so the consultant can answer (without asking the
client) questions like:

- What Hetarios version is this client on?
- What methodology version did we last verify they were running?
- When was the last successful self-test the consultant witnessed?
- What jurisdictions and trust domains are in scope for this client?
- Are they on a methodology overlay that we need to maintain?
- What is their retainer status?

## Adding a deployment

When a paying engagement starts:

1. Copy `_template_deployment.yaml` to `<engagement_code>.yaml` where
   `engagement_code` is the engagement-specific identifier (e.g.
   `acme_h2_2026.yaml`, matching the engagement workspace folder
   name).
2. Fill in the fields. Required fields are marked in the template.
3. Commit the file. Subsequent updates are commits to the same file
   (the git history IS the deployment-change log).

## Updating a deployment record

When something changes — methodology version bump, jurisdiction
added, trust domain expanded, retainer tier moved — edit the YAML
file and commit. The commit message should briefly describe the
change. Do not rewrite history; the audit trail of changes is part
of the record.

## Schema rationale

The schema is intentionally narrow. It captures enough to be useful
without requiring elaborate infrastructure:

- **Identification** — engagement code, system_id, client name
- **Versioning** — Hetarios chassis version, methodology version,
  config schema version
- **Scope** — jurisdictions, trust domains, deployment date
- **Operational** — last consultant-verified self-test, last
  consultant interaction
- **Commercial** — retainer tier, retainer status
- **Methodology overlays** — client-specific KB overlay ID if any
  (most clients will have none; overlays are tracked in
  `methodology_releases/overlay_registry.md`)

What is NOT in the schema:

- Findings (those live in the engagement workspace)
- Detailed configuration (lives in the client's
  `hetarios.config.yaml`; the consultant doesn't track every config
  knob, only what matters for engagement-level coordination)
- Communication history (lives in the engagement workspace)
- Pricing detail (lives in engagement workspace + signed contract)

The schema is consultant-facing operational metadata, not a CRM.

## Privacy

These files are client-confidential. Do not commit to public repos.
