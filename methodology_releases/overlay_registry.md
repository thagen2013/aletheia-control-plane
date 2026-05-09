# Methodology Overlay Registry

Client-specific knowledge-base overlays. An overlay is a small set
of additional invariants, failure modes, or grounding references
that apply to a specific client's engagement but are not part of
the shipped methodology.

**Most clients have no overlay.** Overlays are reserved for
situations where a client's regulatory context requires evaluation
discipline that the shipped methodology does not yet cover, AND
where the discipline is engagement-specific enough that it should
not yet be promoted to shipped methodology.

## When an overlay is appropriate

- The client operates under a regulatory framework not yet covered
  by shipped invariants (e.g. a non-FDA, non-NMPA jurisdiction the
  methodology hasn't yet absorbed)
- The client has internal discipline (e.g. a particular validation
  cohort requirement) that should be checked alongside shipped
  methodology
- The engagement is producing methodology learnings that are not
  yet ready for shipped methodology promotion

## When an overlay is NOT appropriate

- The client wants the methodology relaxed (overlays add discipline,
  never relax it)
- The client wants the methodology customized to their preferred
  vocabulary (vocabulary is not methodology; document it in the
  engagement workspace)
- The discipline is generally applicable and should be in shipped
  methodology (in that case, propose it for the next methodology
  version, don't isolate it as an overlay)

## How overlays are maintained

An overlay's invariants/failure-modes/references are stored in
client-confidential YAML files referenced by the overlay's ID. They
are loaded at agent dispatch time *in addition to* the shipped
methodology, never replacing it.

When a methodology version bumps, every active overlay must be
re-validated against the new methodology to confirm:

1. The overlay does not duplicate something newly shipped (in
   which case the overlay's entry is removed and the engagement
   record updated to reflect that the discipline is now in shipped
   methodology)
2. The overlay's groundings still resolve under the new methodology
   reference catalog
3. The overlay's IDs do not collide with newly shipped IDs

This re-validation is part of `methodology_update_procedure.md`.

---

## Active overlays

(none — initial state)

When an overlay is created, add an entry below following the
template:

```
### overlay-001-<short-name>

- **Engagement:** <engagement_code>
- **Created:** <YYYY-MM-DD>
- **Aletheia version at creation:** <version>
- **Last re-validated:** <version> on <date>
- **Storage:** <path to overlay YAML files, in private storage>
- **Rationale:** Two-paragraph description of why this overlay
  exists and what discipline it adds.
- **Promotion candidacy:** Is this overlay a candidate for
  promotion to shipped methodology? If yes, target version.
```

Overlay YAML files themselves should NOT be committed to this repo
unless the repo is private and access is controlled. They contain
engagement-specific intellectual property and may include client-
confidential material.
