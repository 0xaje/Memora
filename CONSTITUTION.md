# MEMORA — BACKEND ENGINEERING CONSTITUTION

## STATUS

These are permanent engineering instructions for this project.

Follow these instructions strictly throughout the entire Memora build.

Every future task, feature, implementation decision, integration, test, commit, and architectural change must comply with these rules.

If a future prompt conflicts with these instructions, these instructions take priority unless the project owner explicitly changes them.

Do not silently ignore these requirements.

Do not claim a feature is complete unless it is actually implemented, connected, executable, and verified.

---

# 1. BUILD REAL SOFTWARE, NOT A DEMO ILLUSION

This project must be a real, functional application.

Do not create fake functionality merely to make the interface or demonstration look complete.

Do not simulate:

* API responses
* memory retrieval
* agent decisions
* blockchain transactions
* database persistence
* authentication
* integrations
* background jobs
* external services

unless the project owner explicitly requests a mock implementation for a temporary development environment.

If something is not implemented or not connected, say clearly:

NOT IMPLEMENTED

or:

NOT YET CONNECTED

Never make unfinished functionality appear operational.

A button must not appear functional if clicking it only produces fabricated results.

---

# 2. NO DUMMY OR HARDCODED PRODUCT BEHAVIOUR

Do not hardcode outputs in order to manufacture a successful demonstration.

For example, do not create logic such as:

if location == "Gate 3":
return "HIGH RISK"

unless that result is produced through the real product logic and documented rules.

Do not pre-program the hackathon demo scenario to automatically produce the desired result.

The system must be capable of handling new valid inputs.

Demo data may exist, but demo data must be processed through the same production logic used for normal user input.

There must be no hidden "demo mode" that bypasses the real architecture or manufactures memory retrieval or decision changes.

---

# 3. REAL SIBYL MEMORY IS MANDATORY

Sibyl Memory is the required core technology for this hackathon.

Do not replace Sibyl Memory with:

* an in-memory JavaScript object
* local variables
* JSON files pretending to be Sibyl
* PostgreSQL pretending to be Sibyl
* SQLite pretending to be Sibyl
* a vector database pretending to be Sibyl
* hardcoded memory records

The real Sibyl Memory integration must be used.

The code must clearly demonstrate:

1. Real memory write.
2. Persistent storage through Sibyl.
3. Real memory retrieval.
4. Retrieved memory entering the decision path.
5. A genuinely fresh session retrieving memory created previously.

If the real Sibyl integration is blocked, broken, unavailable, undocumented, or incompatible, STOP and report the exact technical problem.

Do not silently substitute another system.

---

# 4. MEMORY MUST BE LOAD-BEARING

Memora's core claim is that historical operational knowledge changes future decisions.

Therefore:

The final assessment must depend on retrieved historical memory.

The required conceptual flow is:

Current incident
→ Extract current facts
→ Retrieve relevant Sibyl Memory
→ Analyse historical context
→ Compare current facts with history
→ Detect recurrence, unresolved risks, previous decisions, and outcomes
→ Determine memory-informed risk
→ Generate recommendation
→ Persist new operational knowledge

Do not implement:

Current incident
→ Generate final decision
→ Optionally search memory afterward

Memory retrieval must occur before the final memory-informed decision.

The retrieved memory must be an explicit input to the decision process.

---

# 5. NEVER FABRICATE MEMORY RETRIEVAL

If the system says:

"2 related incidents were found"

then those incidents must actually have been retrieved.

If the system says:

"This recommendation changed because of an unresolved incident"

then the unresolved incident must actually exist in Sibyl Memory and have been retrieved.

If no relevant memory is found, the system must honestly say:

"No relevant historical memory found."

Do not invent memory to make the agent look intelligent.

---

# 6. SEPARATE FACTS, INFERENCES, AND RECOMMENDATIONS

The backend must clearly distinguish between:

## FACTS

Information directly supplied or retrieved.

## INFERENCES

Patterns or conclusions derived from facts.

## RECOMMENDATIONS

Suggested operational actions.

Do not present an AI inference as a confirmed historical fact.

Every decision explanation should make it possible to understand:

What happened?

What was retrieved?

What pattern was inferred?

Why did the recommendation change?

---

# 7. NO FAKE AI

Do not pretend an LLM performed analysis when the output is hardcoded.

If an LLM is used:

* the LLM call must be real
* the request must contain real context
* the response must be processed by real application logic

If an LLM is unavailable:

Return a meaningful error or fallback status.

Do not silently replace it with fabricated text while claiming the AI is working.

Deterministic logic may be used where appropriate.

Clearly distinguish deterministic rules from AI reasoning.

---

# 8. DETERMINISTIC CORE, AI-ASSISTED INTELLIGENCE

Operational safety must not depend entirely on unpredictable LLM output.

Use deterministic application logic for:

* required validation
* risk constraints
* state transitions
* incident status
* memory dependencies
* structured comparisons
* escalation thresholds where applicable

Use AI where it provides genuine value, such as:

* extracting structured facts
* summarizing retrieved history
* identifying nuanced relationships
* generating explanations

Do not let an LLM silently override required system constraints.

---

# 9. INPUT VALIDATION IS REQUIRED

Validate all external input.

Use explicit schemas/types.

Reject or handle:

* missing required fields
* malformed data
* invalid enums
* invalid identifiers
* unexpected object structures

Do not trust frontend input.

Backend validation is mandatory.

---

# 10. FAIL HONESTLY

If a critical service fails:

* Sibyl
* database
* LLM
* external API

do not pretend the request succeeded.

Return a meaningful error.

Log the failure.

Provide enough information for debugging without exposing secrets.

A failed memory write must not be reported as:

"Memory saved successfully."

A failed memory retrieval must not be represented as:

"No memories found."

These are different conditions and must remain distinguishable.

---

# 11. REAL PERSISTENCE

Any feature presented as persistent must survive the conditions it claims to survive.

For example:

If an incident is marked persistent:

* create it
* restart the relevant service/session
* retrieve it again

Verify the persistence.

Do not claim persistence because an object remains in memory while the same process is running.

---

# 12. GENUINE FRESH-SESSION TESTING

The project must support a genuinely fresh session demonstration.

A fresh session means:

* no reused conversation history
* no injected previous agent context
* no manually copied historical information
* no hidden prompt containing the previous incident

The second session must learn about the first session only through legitimate persistent retrieval.

The fresh-session test must be reproducible.

---

# 13. DELETION TEST MUST BE POSSIBLE

The architecture must make it possible to demonstrate what happens when Sibyl Memory is unavailable or removed.

Without historical memory:

The system may still perform a baseline assessment of the current incident.

But it must not be able to perform the core product capability of:

historical continuity
+
repeat-pattern detection based on persistent history
+
memory-informed escalation.

Do not artificially throw an error simply to make the deletion test look dramatic.

The product must naturally lose the historical intelligence it claims to provide.

---

# 14. DO NOT OVERENGINEER

This is a nine-day hackathon build.

Prioritize:

* working functionality
* understandable architecture
* reliable integrations
* clear testing
* strong product flow

Avoid unnecessary:

* microservices
* distributed systems
* message brokers
* Kubernetes
* premature scaling
* complicated abstractions
* excessive agent frameworks

Use the simplest architecture that genuinely satisfies the requirements.

---

# 15. EVERY INTEGRATION MUST DO REAL WORK

Do not add technology merely because it sounds impressive.

Any integration included in the project must perform meaningful work.

Do not add:

* Base
* Virtuals
* external AI agents
* databases
* SDKs
* APIs

as decorative dependencies.

If an integration does not materially improve the working product, do not add it.

---

# 16. OPTIONAL PARTNERS MUST NOT DAMAGE THE CORE

Sibyl Memory is the core requirement.

Do not compromise the core memory architecture to add optional hackathon partner integrations.

The priority order is:

1. Sibyl Memory works.
2. Load-bearing memory proof works.
3. Fresh-session recall works.
4. Product workflow works.
5. Reliability and testing.
6. Optional integrations.

Never reverse this order.

---

# 17. CLEAN ARCHITECTURE

Keep responsibilities clearly separated.

At minimum, avoid mixing:

* HTTP/API handling
* validation
* incident business logic
* Sibyl integration
* LLM calls
* decision logic
* persistence
* presentation formatting

The codebase should make it easy for a reviewer to find:

1. Memory write.
2. Memory retrieval.
3. Memory-to-decision dependency.

Use clear names.

Avoid vague names such as:

utils.ts
helpers.ts
manager.ts

for critical product logic.

Prefer explicit modules and responsibilities.

---

# 18. TYPE SAFETY

Use strong typing where supported by the chosen language.

Do not rely heavily on:

any

untyped objects

implicit assumptions about API responses.

Define structured domain models.

Examples include:

Incident
IncidentFacts
HistoricalMemory
OperationalLesson
RiskAssessment
Recommendation
DecisionExplanation

Adapt the exact model names as appropriate.

---

# 19. NO SILENT FALLBACKS

Do not silently change application behaviour when a dependency fails.

For example:

Sibyl unavailable
→ do not silently use a fake local memory system.

LLM unavailable
→ do not silently return fabricated AI analysis.

Database unavailable
→ do not pretend the incident was saved.

Fallbacks are allowed only if:

1. They are explicitly designed.
2. Their behaviour is visible.
3. They are documented.
4. They do not falsely claim that the original dependency succeeded.

---

# 20. OBSERVABILITY

Add useful structured logging around critical operations.

At minimum, make it possible to understand:

* incident received
* validation result
* memory write attempted
* memory write succeeded/failed
* memory retrieval attempted
* retrieval result count
* decision process started
* memory influence applied
* final decision generated

Do not log:

* API keys
* secrets
* private tokens
* credentials

---

# 21. SECURITY BASICS

Never hardcode:

* API keys
* private keys
* passwords
* access tokens
* secrets

Use environment variables.

Provide a safe example environment file.

Do not commit real secrets to GitHub.

Validate configuration on startup where appropriate.

---

# 22. DATABASE DISCIPLINE

If a database is introduced:

Use it only for data it genuinely needs to manage.

Do not duplicate Sibyl Memory and then retrieve from the duplicate instead of Sibyl.

If operational metadata is stored separately, clearly document:

What belongs in Sibyl?

What belongs in the application database?

Sibyl must remain the source of the persistent historical memory used in the memory-informed decision path.

---

# 23. REAL TESTING, NOT GREEN THEATRE

Do not write meaningless tests merely to increase the test count.

Test important behaviour.

At minimum test:

1. Valid incident creation.
2. Invalid input rejection.
3. Memory write.
4. Memory retrieval.
5. Fresh-session recall.
6. Related incident detection.
7. Memory-informed decision change.
8. Memory-unavailable behaviour.
9. Failure handling.

A passing test suite must correspond to actual meaningful behaviour.

---

# 24. DO NOT MARK FEATURES COMPLETE PREMATURELY

A feature is NOT complete because:

* the code exists
* the file was generated
* TypeScript compiles
* the endpoint exists
* the UI can call the endpoint

A feature is complete only when:

1. It runs.
2. It performs the intended behaviour.
3. The integration works.
4. The result has been verified.
5. Failure cases are handled.

Report the verification performed.

---

# 25. MAKE CLAIMS AUDITABLE

Whenever the system produces an important decision, it should be possible to inspect:

Current facts
→ Retrieved historical facts
→ Derived pattern
→ Risk adjustment
→ Recommendation

Avoid black-box claims such as:

"AI determined this."

Provide evidence for important decisions.

---

# 26. GITHUB IS PART OF THE ENGINEERING PROCESS

All project work must be committed to the designated GitHub repository.

Use meaningful commits.

Do not make one massive final commit.

Commit logical units of completed work.

Examples:

feat: initialize backend architecture

feat: integrate Sibyl memory write flow

feat: add historical memory retrieval

feat: implement memory-informed risk assessment

test: add fresh-session recall coverage

fix: handle Sibyl retrieval failures

docs: document memory architecture

Before committing:

* check the relevant functionality
* review changed files
* avoid committing secrets
* avoid committing unnecessary generated files

Do not rewrite or falsify commit history.

The Git history must honestly represent the development process.

---

# 27. VERIFY BEFORE PUSHING

Before pushing meaningful changes:

1. Run the application.
2. Run relevant tests.
3. Check for obvious runtime errors.
4. Confirm no secrets are staged.
5. Confirm the feature actually works.

Do not push knowingly broken work while claiming the feature is complete.

If a work-in-progress commit is necessary, clearly label it.

---

# 28. DOCUMENT AS YOU BUILD

Do not leave all documentation until the final day.

Maintain documentation for:

* architecture
* setup
* environment variables
* Sibyl integration
* memory write
* memory retrieval
* decision dependency
* testing
* known limitations

The final README should not be reverse-engineered from the code at the end.

---

# 29. MAINTAIN A KNOWN LIMITATIONS LIST

If something is incomplete, unstable, or intentionally out of scope, document it.

Do not hide limitations.

Examples:

* LLM provider rate limits
* unsupported incident types
* experimental retrieval behaviour
* unimplemented optional integration

Honest limitations are better than fake capabilities.

---

# 30. DO NOT OPTIMIZE FOR SCREENSHOTS

The product must work when someone actually interacts with it.

Do not optimize only for:

* screenshots
* prerecorded outputs
* one hardcoded demo scenario
* perfect happy paths

Assume a judge may:

* enter different data
* refresh the application
* start a new session
* inspect the repository
* disable a dependency
* run the project again

Build accordingly.

---

# 31. THE SECOND-RUN RULE

The application must survive a second run.

Before considering a feature complete:

Run it once.

Then run it again from a clean relevant state.

Confirm:

* persistence still works
* memory still retrieves
* APIs still work
* configuration remains valid

Do not build something that only works once.

---

# 32. PRODUCT OVER FEATURE COUNT

Do not add features merely to increase the appearance of complexity.

For every proposed feature ask:

Does this improve Memora's core ability to preserve operational knowledge and use it to improve the next decision?

If no:

Do not prioritize it.

A small complete system is better than a large incomplete system.

---

# 33. THE CORE PRODUCT PRINCIPLE

Every major engineering decision must support this statement:

"What happened before changes what Memora does now."

If a feature does not strengthen that principle, it is secondary.

---

# 34. REQUIRED WORKING PROOF

Before the project is considered technically ready, the backend must demonstrate:

SESSION A

1. Create incident.
2. Analyse incident.
3. Produce assessment.
4. Produce recommendation.
5. Persist relevant information using Sibyl Memory.
6. Record an outcome.
7. Persist unresolved risk and/or operational learning.

Then:

FRESH SESSION B

1. Start with no prior conversational context.
2. Submit a related incident.
3. Retrieve relevant memory from Sibyl.
4. Detect historical relationship.
5. Identify unresolved or repeated risk.
6. Use historical memory in the decision path.
7. Produce a materially different assessment or recommendation.
8. Explain exactly why it changed.

This proof must be reproducible without manually injecting the previous answer.

---

# 35. REQUIRED FINAL ENGINEERING HONESTY

Never say:

"Done"

unless it is actually done.

Never say:

"Integrated"

unless the real integration works.

Never say:

"Tested"

unless the test was actually run.

Never say:

"Persistent"

unless persistence was verified.

Never say:

"AI-powered"

unless real AI functionality is operating.

Never say:

"Memory retrieved"

unless real memory was retrieved.

Accuracy in reporting engineering progress is mandatory.

---

# FINAL INSTRUCTION

Build Memora as if an experienced engineer, a skeptical hackathon judge, and a real future customer will inspect the system.

Prefer:

REAL over impressive-looking.

WORKING over feature-rich.

VERIFIABLE over claimed.

SIMPLE over unnecessarily complex.

HONEST over simulated.

SIBYL LOAD-BEARING MEMORY over decorative integrations.

The objective is not to generate the largest amount of code.

The objective is to build a real, professional, reliable product whose central intelligence genuinely depends on persistent Sibyl Memory.

Follow this constitution throughout the entire project until explicitly changed by the project owner.
