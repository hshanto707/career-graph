# Conclusion & Future Work

> Thesis closing chapter draft, per `docs/current-status.md` Milestone 5.
> Reconciles against `docs/system-design.md` §2 ("Project Scope" — the
> IS/IS NOT/Post-Capstone diagram) and `docs/research-contribution.md`
> (the six claimed contributions). Companion to
> `docs/evaluation-chapter.md` (results this conclusion summarizes) and
> `docs/discussion-limitations.md` (limitations this future-work section
> responds to point by point).

---

## Conclusion

CareerGraph set out to build an explainable, graph-based career guidance
platform for students, combining a knowledge-graph-backed intelligence
engine with a trained, evaluated custom AI model — and, per
`docs/system-design.md` §2, explicitly *not* to build a chatbot, a resume
builder, or a black-box ML system. That scope held throughout the build:
every recommendation, gap score, and roadmap the system produces traces
back to inspectable graph structure and deterministic agent logic
(`docs/research-contribution.md` Contribution 3), and the one component
that is a trained neural network (the GraphSAGE link predictor) is
evaluated openly against a hand-tuned baseline rather than presented as an
unquestionable black box.

Against `docs/research-contribution.md`'s six claimed contributions, the
project delivers on all six as actually built and verified, not merely
designed:

1. **Persistent, proficiency-weighted student graph node** — `Student`
   nodes with typed `HAS_SKILL {proficiency, years}` edges, live in Neo4j.
2. **Ordered learning roadmap via prerequisite graph traversal** —
   `PathFinderAgent`'s BFS + topological sort over `LEADS_TO`, verified end
   to end (with the caveat in Limitation #2 that `LEADS_TO` itself is
   currently synthetic).
3. **LLM as a decoupled, optional explainability layer** — proven, not
   just designed: the system ran with `LLM_PROVIDER=none` for the entire
   build and the shipped defense configuration, and every narrative shown
   to a user throughout that time was the template fallback, working
   correctly.
4. **Continuous skill normalization pipeline** — `NormalizationAgent`'s
   synonym + rapidfuzz matching, exercised against the full 10,000-row
   dataset (55,428 skill edges written, 493 instances flagged for review
   out of injected messy input).
5. **Live, re-ingestible knowledge base** — the admin CSV-ingest endpoint
   and `GraphService`'s idempotent `MERGE`-based writes, hardened during
   this project by fixing a real data-integrity bug (Implementation
   chapter §4.1) that would have undermined this exact claim if left
   unfixed.
6. **Trained GNN link-prediction model as a reranking layer, with an
   explicit algorithmic baseline** — trained, evaluated honestly (the
   baseline wins on `REQUIRES`, disclosed rather than hidden), and — as of
   this project's final hardening phase — actually wired into a live
   request path and verified against a real deployment, not left as an
   unused offline artifact.

That last point is worth stating plainly as the project's central
methodological lesson, because it very nearly wasn't true: for a
substantial portion of the build, the GNN was fully trained and evaluated
but never called by any live code path — a state that would have looked,
to a reader of the evaluation report alone, indistinguishable from a fully
integrated system. Closing that gap, and the further gap uncovered only by
deploying the integrated system for real (Implementation chapter §4.3),
is the concrete evidence behind this project's broader claim: a green test
suite and a good offline metric are each necessary, and neither is
sufficient, for the claim "this system works."

## Future Work

Ordered roughly by how directly each follows from a limitation already
identified in `docs/discussion-limitations.md`, rather than by ambition —
the nearer items are scoped continuations of this project, not a wishlist.

### Near-term (directly closes a stated limitation)

1. **Real Kaggle job-postings data + real O*NET/ESCO skill taxonomy**
   (`docs/discussion-limitations.md` §1, `docs/data-sources.md`). Concrete
   next step already documented: source a current Kaggle job-postings
   dataset, build the skill-extraction pre-processing step most such
   datasets need (they rarely ship a clean `skills_required` column), and
   regenerate `onet_skills.csv`/`synonyms.json` from O*NET's `Technology
   Skills.txt`/`Skills.txt` or an ESCO export. None of the ingestion,
   normalization, or GNN training code would need to change — only the
   input files.
2. **A real `LEADS_TO` (skill-prerequisite) data source**
   (`docs/discussion-limitations.md` §2). Two concrete candidates already
   identified: derive prerequisite pairs from structured course-curriculum
   ordering, or from historical career-progression data (which skills are
   commonly acquired after which, across real career trajectories). Either
   would let the GNN's already-promising `LEADS_TO` AUC-ROC result (0.679
   vs. random-chance 0.500) be evaluated against ground truth worth
   trusting, rather than a synthetic heuristic.
3. **Richer GNN input features for `REQUIRES`**
   (`docs/evaluation-chapter.md` §1.3). The current encoder uses a learned
   embedding table per node as its only input feature. Text embeddings of
   job descriptions/skill definitions are the most plausible next step to
   close the gap with the algorithmic baseline — the architecture (2-layer
   heterogeneous GraphSAGE) already supports richer input features without
   redesign; only the encoder's input layer would change.
4. **A real LLM smoke test** (deliberately deferred, not abandoned —
   `docs/current-status.md` Milestone 2). Low effort whenever a demo moment
   specifically calls for it: configure a real `ANTHROPIC_API_KEY` and
   capture real `ReasoningAgent` output for at least one profile, without
   changing any code.

### Medium-term (system-design.md §2's Post-Capstone Scope, still valid)

5. **Multi-region, multi-language job market support** — the current
   dataset (real or synthetic) is US/Canada-centric and English-only; this
   compounds with item #1 above, since most public real job datasets skew
   the same way, making this a genuinely separate effort from "get real
   data."
6. **Real-time job ingestion** — the admin CSV-ingest endpoint is
   functional but manually triggered; a scheduled/streaming ingestion
   pipeline would let market-demand signals track a live job market instead
   of a point-in-time snapshot.
7. **Advanced ranking models** — beyond the richer-input-features work in
   #3, exploring alternative GNN architectures (e.g. attention-based
   encoders) or a learned reranking policy (rather than the current fixed
   `0.6/0.15/0.25` blend weights) once real data (#1) makes such tuning
   meaningful.
8. **A RAG-based market insights assistant** — a natural extension once
   real-time ingestion (#6) exists: retrieval-augmented generation over
   live market data, layered on top of (not replacing) the existing
   deterministic `MarketAgent`, consistent with this project's principle
   that an LLM narrates already-computed results rather than replaces them.
9. **Resume parsing** — an alternative profile-entry path (parse an
   uploaded resume into structured skills/experience) rather than the
   current manual entry, explicitly out of scope for the capstone per
   `system-design.md` §2's "This Project is NOT" list, retained here for
   completeness since it's a natural product extension.

### Infrastructure hardening (identified during this project's own build)

10. **A distributed rate limiter for login lockout** — the current
    implementation (`backend/app/core/login_lockout.py`) is an honest,
    explicitly-documented in-process control, sufficient to demonstrate
    the protection exists but not production-grade across multiple
    backend replicas; a real deployment would back this with Redis or the
    existing Postgres instance.
11. **Frontend bundle code-splitting** — the production build is a single
    ~575 KB chunk; dynamic `import()` for route-level code-splitting was
    noted as a real, minor performance improvement (not a correctness
    issue) and deprioritized against the higher-leverage work in
    `docs/current-status.md`'s milestone sequence.
12. **Reconciling the two parallel `docker-compose.yml` configurations**
    (Implementation chapter §4.4) — both are now correct and both were
    verified live, but maintaining two independently-configured stacks is
    itself a standing risk of exactly the kind of drift that was found and
    fixed during this project's hardening phase; consolidating them (or
    generating one from the other) would remove that risk permanently
    rather than relying on periodic re-verification.
