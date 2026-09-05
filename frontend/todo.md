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

- [x] Audit whether the verified FastAPI backend exists in this repository, another project, or neither; it exists in the GitHub repository under `memora/`.
- [x] Identify the authoritative backend process, API base URL, endpoints, source files, and verified commit if available; documented in the Phase 2.5 architecture audit.
- [x] Write `docs/PHASE_2_5_ARCHITECTURE_AUDIT.md` with the findings and remaining integration notes.
- [x] Add a typed REST client against the verified contract in `client/src/lib/memora-api.ts`.
- [x] Probe real memory status on workspace load and preserve explicit unavailable/error states; header refinement remains a follow-up.
- [x] Connect real incident analysis and expose backend-provided current incident, baseline, memory, and decision fields; provenance rendering remains a follow-up.
- [x] Connect real memory search with loading, empty, unavailable, malformed-response, and error states.
- [x] Add the typed outcome recording client boundary; operator outcome form wiring remains a follow-up until a live analysis context is present.
- [x] Guard against stale request state, duplicate submissions during analysis/search, unsafe rendering, leaked paths, and exposed credentials in the integrated scope.
- [x] Document the real endpoint/session verification prerequisite without fabricating proof; the backend process is outside the current managed frontend preview.
- [x] Add regression coverage for the current contract/state boundary; existing suite remains green.
- [x] Re-review todo.md and save a corrected checkpoint before delivery; GitHub main was also verified at the pushed commit.

## GitHub Delivery

- [ ] Inspect `https://github.com/0xaje/Memora` and compare its remote history with the local project.
- [ ] Confirm no secrets or generated deployment artifacts are included in the commit.
- [ ] Commit the completed Memora workspace with a descriptive message.
- [ ] Push the commit to the requested GitHub remote without overwriting unrelated work.
- [ ] Verify the remote branch and commit after push.

## Direct Main Delivery

- [x] Confirm authenticated GitHub access for `0xaje/Memora`.
- [x] Integrate the completed frontend into `frontend/` while preserving the FastAPI backend.
- [x] Commit the integrated workspace to `main` with no secrets, node_modules, dist, or local logs.
- [x] Push directly to `main` without force-overwriting unrelated history.
- [x] Verify the remote `main` commit and final tree; remote main is `cc180fa`.

## Phase 2.5 Follow-up Corrections

- [x] Bind fetched Sibyl memory status to visible header and workspace indicators instead of hardcoded labels.
- [x] Add request-version guards so stale analysis and memory-search responses cannot overwrite newer state.
- [x] Add Vitest coverage for the typed REST client and live status, analysis, and search state transitions.
- [x] Re-run type-check, tests, and build after the corrections; TypeScript, 5 test files/9 tests, and production build passed.
- [x] Save a fresh webdev checkpoint for the post-integration state and push the follow-up commit to GitHub main.

## Final Follow-up QA

- [x] Add frontend coverage for visible Home live states: Sibyl status, incident analysis success/error, and memory search success/empty/error.
- [x] Save a fresh webdev checkpoint after the Phase 2.5 follow-up corrections.
- [x] Commit and push the follow-up correction changes to GitHub main, then verify the new remote commit SHA.

## Branch-only GitHub Delivery

- [ ] Create one dedicated branch from the already-pushed repository state without pushing `main` again.
- [ ] Commit all prepared frontend, REST integration, tests, audit, and tracker changes on that branch.
- [ ] Push only the dedicated branch to `0xaje/Memora`.
- [ ] Verify the remote branch SHA and confirm `main` was not modified during this delivery.
