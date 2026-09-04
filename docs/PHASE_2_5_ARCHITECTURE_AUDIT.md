# Memora Phase 2.5 Architecture Audit

## Finding

The authoritative Memora backend is present in this repository under `memora/` and is a FastAPI application. The verified product API is not a tRPC router. The frontend therefore must call the domain REST API directly and must not recreate the product contract through Drizzle or duplicate tRPC procedures.

## Repository layout

| Concern | Authoritative location | Finding |
|---|---|---|
| FastAPI application | `memora/api/app.py` | Present in the existing repository |
| Incident analysis | `memora/api/routes_incidents.py` | `POST /api/incidents/analyze` |
| Memory status and search | `memora/api/routes_memory.py` | `GET /api/memory/status`, `GET /api/memory/search` |
| Outcome recording | `memora/api/routes_outcomes.py` | `POST /api/outcomes` |
| REST contract | `docs/API_CONTRACT.md` | Frozen response and error shapes |
| Frontend integration guidance | `docs/FRONTEND_INTEGRATION.md` | FastAPI default at `http://localhost:8000` |
| React operations console | `frontend/` | Added by this commit from the completed Memora workspace |

## Processes and URLs

The backend is started from the repository root with `PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload`. The frontend is a Vite/Express web project under `frontend/`; its API base is configured with `VITE_MEMORA_API_URL`, defaulting to `http://localhost:8000` for local development.

The domain API exposes `GET /health`, `GET /api/memory/status`, `POST /api/incidents/analyze`, `POST /api/outcomes`, and `GET /api/memory/search`. The current frontend now contains a typed REST boundary in `frontend/client/src/lib/memora-api.ts` and uses that boundary for incident analysis, memory status probing, and memory search. Authentication remains available through the existing Manus scaffold but is not used as a substitute for the Memora domain API.

## Integrity and security findings

The Phase 2.5 integration does not add a second memory database, migrate Sibyl data, create mock responses, hardcode operational history, expose a memory bypass control, or fabricate IDs, timestamps, decisions, metrics, or provenance. Backend-provided fields are displayed when present; missing fields are labeled as not provided by the backend. The REST client surfaces network failures, standardized API errors, and malformed response bodies explicitly.

The backend contract intentionally has no Phase 1 authentication requirement. The frontend does not add simulated tokens. No filesystem path, credential, tenant secret, `node_modules`, build output, or local log is included in the integrated frontend directory.

## Remaining integration work

Outcome recording is represented in the typed client but still needs its final operator form wired to the live analysis context. The provenance panel should be connected to the returned analysis object in the next UI pass so the four backend-provided provenance strings are rendered directly. Real Session A/Session B and deletion-proof verification require a running FastAPI/Sibyl environment and are not claimed by this repository-only commit.
