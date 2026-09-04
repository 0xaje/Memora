# Project TODO

- [x] Review the attached product brief and map the required operational concepts to frontend sections.
- [x] Review the available project scaffold and existing typed tRPC/auth contracts before adding UI data flows.
- [x] Implement the responsive blueprint-style operations workspace shell and navigation.
- [x] Implement incident intake with explicit empty, unavailable, and error states; typed incident-analysis mutation remains a backend integration gap.
- [x] Implement current incident, baseline-versus-memory decision transformation, historical memory, inference, decision, and provenance detail views with honest unavailable states until backend procedures exist.
- [x] Track outcome recording and post-outcome learning refresh as a remaining backend integration; the UI stays locked until the real contracts are available.
- [x] Implement optional evidence-only AI-assisted summary guardrails with clear unavailable labeling and no invented activity.
- [x] Add or update Vitest coverage for the implemented backend/frontend contract behavior.
- [x] Verify responsive layouts, interactions, visual hierarchy, accessibility, and browser console/network health.
- [x] Resolve any verified bugs found during implementation and verification; no verified bugs remain.
- [x] Document remaining integrations and unavailable backend capabilities explicitly in the UI and project notes.
- [x] Review todo.md and mark all completed items before the final checkpoint; backend integrations remain explicitly pending.

## QA Follow-up

- [x] Add frontend Vitest coverage for Home/workspace unavailable, empty, and error-state rendering.
- [x] Document keyboard navigation, visible focus states, and primary interactions; semantic buttons/labels and visible focus styles are present, and the three primary views were exercised in preview.
- [x] Retest after coverage and interaction review; type-check and all four tests passed after the frontend test was added.
- [x] Only mark final todo review complete after all completed items are justified; remaining backend integrations are left pending below.

## QA Results So Far

- [x] Desktop screenshot captured.
- [x] Mobile screenshot captured.
- [x] TypeScript check passed.
- [x] Vitest suite passed.
- [x] Production build passed.
- [x] Frontend interaction/state tests added.
- [x] Keyboard/focus pass recorded.
- [x] Final QA review complete for the implemented frontend scope; product API and outcome integrations remain pending.

## Backend Availability

- [x] Typed auth identity is consumed through `trpc.auth.me`.
- [x] Incident analysis procedure status checked; not mounted in the current backend router and documented as unavailable.
- [x] Memory search and status procedure status checked; not mounted in the current backend router and documented as unavailable.
- [x] Outcome recording procedure status checked; not mounted in the current backend router and documented as unavailable.
- [x] Evidence-only summary procedure status checked; not mounted in the current backend router and documented as unavailable.

## Integrity Checks

- [x] Unsupported records render as unavailable.
- [x] Unsupported metrics are not invented.
- [x] AI summary is not simulated and is clearly labeled unavailable.
- [x] No mock activity or demo records added.
- [x] Accidental write-marker bug fixed; type-check and build pass.

## Open QA Notes

- [x] Verify focus rings, keyboard activation, dismissible notices, and mobile overflow.
- [x] Keep outcome and product API work pending until typed backend procedures are available.
- [x] Do not checkpoint until the QA follow-up items are resolved or explicitly left pending; this condition is satisfied and the final state is now ready.

## Phase 2.5 Correction Work

- [ ] Audit whether the verified FastAPI backend exists in this repository, another project, or neither.
- [ ] Identify the authoritative backend process, API base URL, endpoints, source files, and verified commit if available.
- [ ] Write `docs/PHASE_2_5_ARCHITECTURE_AUDIT.md` with the findings and any blocker.
- [ ] Add a typed REST client only if the authoritative backend is reachable and its contract can be verified.
- [ ] Connect real health and memory status to the Sibyl header state without assumptions.
- [ ] Connect real incident analysis and expose backend-provided current incident, baseline, memory, decision, inference, and provenance fields.
- [ ] Connect real memory search with loading, empty, unavailable, malformed-response, and error states.
- [ ] Connect real outcome recording and learning refresh only after a decision exists and the backend confirms success.
- [ ] Guard against stale responses, duplicate submissions, unsafe rendering, leaked paths, and exposed tenant or credential data.
- [ ] Run real endpoint/session verification only when the authoritative backend is available; otherwise document the exact blocker without fabricating proof.
- [ ] Add regression coverage for the typed REST boundary and real-data state transitions.
- [ ] Re-review todo.md and save a corrected checkpoint after all achievable work is complete.

## GitHub Delivery

- [ ] Inspect `https://github.com/0xaje/Memora` and compare its remote history with the local project.
- [ ] Confirm no secrets or generated deployment artifacts are included in the commit.
- [ ] Commit the completed Memora workspace with a descriptive message.
- [ ] Push the commit to the requested GitHub remote without overwriting unrelated work.
- [ ] Verify the remote branch and commit after push.

## Direct Main Delivery

- [ ] Confirm authenticated GitHub access for `0xaje/Memora`.
- [ ] Integrate the completed frontend into the existing repository tree while preserving the FastAPI backend.
- [ ] Commit the integrated workspace to `main` with no secrets, node_modules, dist, or local logs.
- [ ] Push directly to `main` without force-overwriting unrelated history.
- [ ] Verify the remote `main` commit and final tree.
