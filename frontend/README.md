# Memora Operations Console

This directory contains the React/Tailwind operations workspace for Memora. It preserves the architectural blueprint interface while consuming the authoritative FastAPI domain API from the parent repository.

## Local development

Start the backend from the repository root with:

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Then start this frontend from `frontend/` with:

```bash
pnpm install
pnpm dev
```

Set `VITE_MEMORA_API_URL` when the backend is not running at `http://localhost:8000`. The typed REST boundary lives in `client/src/lib/memora-api.ts` and covers health, memory status, incident analysis, memory search, and outcome recording.

The interface never seeds or fabricates incidents, memory records, metrics, timestamps, decisions, or provenance. If the backend is unavailable or a field is absent, the UI shows an explicit state instead.
