# Research Artifact Contract

Stage 7C applies this contract to every **new or refreshed** research artifact. Historical dated evidence stays historical and is not rewritten only to add metadata.

Every research artifact must make these four facts explicit:

- **as_of** — the observation/data time the artifact describes, not merely the file-write time.
- **provenance** — the source URLs, provider/readback artifact, registry, or exact evidence inputs used.
- **uncertainty** — known walls, missing reads, confidence limits, unverified claims, or an explicit `none_known`.
- **refresh_target** — the event/cadence that makes the artifact due again, such as the next Research Seat run, a changed upstream HEAD/release, the Friday accountability pass, or an explicit task.

For Markdown artifacts, include a short `Research metadata` block near the top with those four labels. For JSON artifacts, expose the same information under top-level `artifactMeta` using `asOf`, `provenance`, `uncertainty`, and `refreshTarget`.

Metadata is evidence context, not policy authority. It does not authorize an upgrade, send, publish, deletion, purchase, or any other external effect.

The existing **Velvet Research Seat** remains the research router. Cheap upstream change detection runs first. Deep review is required only when the current HEAD/release lacks an exact bound review or an explicit task asks for review. A pending update with a current exact review is reused rather than re-reviewed merely because it remains pending adoption.

GitHub Actions may verify freshness, build indexes, or execute machine workflows on its own schedule. Those schedules do not replace the live protected Grok Bot clock authority for owner-facing routines.
