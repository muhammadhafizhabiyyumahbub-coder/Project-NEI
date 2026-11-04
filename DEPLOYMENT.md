# NEI Deployment Guide

## Prerequisites

- Python 3.13
- Node.js 20+
- Windows 11 (single-user local deployment)

## Install

```bash
# Backend
cd D:\Project NEI
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm install
```

## Configuration

Create `.env` in project root:

```env
NEI_SESSION_SECRET=my-strong-secret
NEI_LLM_PROVIDER=openai
NEI_LLM_API_KEY=sk-...
NEI_LLM_MODEL=gpt-4o-mini
```

## Build Frontend

```bash
cd apps/ui
npm install
npm run build
```

Output: `apps/ui/dist/`

## Run (Production)

```bash
# From project root
NEI_SESSION_SECRET=my-strong-secret uvicorn nei.main:app --host 127.0.0.1 --port 8000
```

FastAPI serves `apps/ui/dist/` statically at `/`.

## Run (Development)

```bash
# Terminal 1 — backend
NEI_SESSION_SECRET=test-secret uvicorn nei.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend dev server
cd apps/ui
npm run dev
```

Open `http://127.0.0.1:5173`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check (public) |
| POST | `/api/v1/auth/session` | Mint session cookie |
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}/tasks` | List tasks |
| POST | `/api/v1/projects/{id}/tasks` | Create task |
| GET | `/api/v1/tasks/{id}` | Get task |
| POST | `/api/v1/tasks/{id}/cancel` | Cancel task |
| GET | `/api/v1/tasks/{id}/events` | SSE live events |
| GET | `/api/v1/connectors` | List connectors |
| POST | `/api/v1/connectors/{id}/probe` | Probe connector |
| GET | `/api/v1/evidence/sources` | List evidence |
| POST | `/api/v1/evidence/search` | Search evidence |
| GET | `/api/v1/formulas` | List formulas |
| POST | `/api/v1/calculations` | Run calculation |

## Testing

```bash
python -m pytest tests/ -v
```

## OpenAPI Schema

- Live: `GET http://127.0.0.1:8000/openapi.json`
- Snapshot: `apps/ui/openapi.json` (refresh with `npm run generate-types` in `apps/ui`)
- Frontend types: `apps/ui/src/api/types.ts` (generated via `npx openapi-typescript`)

## CORS (Dev)

Backend `CORSMiddleware` allows `localhost:5173`, `127.0.0.1:5173`, `localhost:8000`, `127.0.0.1:8000` with credentials. The frontend client (`apps/ui/src/api/client.ts`) hardcodes `http://localhost:8000/api/v1` — Vite dev proxy `/api` → `:8000` is available but the client bypasses it; direct cross-origin works because CORS allows both origins. For production, the backend serves `apps/ui/dist/` at `/` (same-origin), so CORS is irrelevant.

## Connector Status (Backend Change)

`list_connectors()` now joins the `connectors` DB table and returns `status` (`DETECTED`, `NOT_FOUND`, `UNKNOWN`, or `null` if never probed). The frontend `Connector` type includes optional `status?: string | null`.

## Browser UI (Manual)

Verified via in-app browser at `http://127.0.0.1:5173`:
- Dashboard loads, health badge shows `ok`
- Projects page renders form + list (no console errors)
- Create project → lands on ProjectDetail
- Create task → task list shows it
- Cancel task → state `cancelled`

Playwright e2e (`apps/ui/e2e/happy-path.spec.ts`) is written but Chromium download is blocked by network/CDN timeout; run `npx playwright install chromium` when network recovers.
