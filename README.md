# ArchOpt — AI Campus Layout Optimizer Backend

Backend, database, and orchestration service for the ArchOpt AI Campus Planning system, built in accordance with the **Technical Architecture & 6-Person Execution Contract**.

## Overview
ArchOpt automates university campus spatial planning using AI layout generation and multi-objective evolutionary optimization.

- **FastAPI**: Asynchronous REST backend hosting all 17 contract APIs.
- **PostgreSQL & SQLAlchemy**: Relational persistence across 8 contract tables.
- **Alembic**: Database migrations management.
- **Pydantic v2**: Strict request/response validation with camelCase aliasing matching the frontend/Blender contracts.
- **Bcrypt & JWT**: Secure password hashing and token-based Bearer authentication.
- **ML Bridge**: Clean architectural boundary interfacing Person 4 with Person 1 (Graph Builder), Person 2 (GNN Generator), and Person 3 (NSGA-II Optimizer).

---

## Quickstart

### 1. Requirements
- Python 3.11+
- PostgreSQL (Docker or local installation)

### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Migration
```bash
python -m alembic upgrade head
```

### 4. Running the Server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
- Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
- OpenAPI JSON Specification: `http://localhost:8000/openapi.json` (also stored in `docs/openapi.json`)

### 5. Running Tests
```bash
pytest backend/tests -v
```

---

## Configuration & Pipeline Modes

Configured via environment variables or `.env`:
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5433/campus_planner`).
- `SECRET_KEY`: Secret string for signing JWT tokens.
- `PIPELINE_MODE`:
  - `mock` (default): Employs deterministic contract-compliant candidate generation for frontend/Blender local integration.
  - `real`: Dispatches execution to real P1 (`ml.dataset.graph_builder`), P2 (`ml.inference.generate`), and P3 (`optimization.optimizer`) modules. If any module fails or is missing, raises `422 GENERATION_FAILED`.

---

## 17 Master REST APIs

| Method | Endpoint | Description |
|:---:|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login and receive Bearer JWT |
| `POST` | `/api/projects` | Create new campus project |
| `GET` | `/api/projects/{projectId}` | Get project details |
| `PUT` | `/api/projects/{projectId}` | Update project |
| `DELETE` | `/api/projects/{projectId}` | Delete project |
| `POST` | `/api/projects/{projectId}/requirements` | Save campus requirements |
| `GET` | `/api/projects/{projectId}/requirements` | Get campus requirements |
| `POST` | `/api/projects/{projectId}/buildings` | Add building to project |
| `GET` | `/api/projects/{projectId}/buildings` | List project buildings |
| `POST` | `/api/projects/{projectId}/constraints` | Add spatial constraint |
| `GET` | `/api/projects/{projectId}/constraints` | List project constraints |
| `POST` | `/api/projects/{projectId}/layout-runs` | Trigger layout generation run |
| `GET` | `/api/projects/{projectId}/layouts` | List generated layout candidates |
| `GET` | `/api/layouts/{layoutId}` | Get single layout detail |
| `POST` | `/api/layouts/{layoutId}/select` | Mark layout as selected plan |
| `GET` | `/api/layouts/{layoutId}/blueprint` | Export Blender 3D blueprint JSON |

See `ARCHOPT_TEAM_INTEGRATION_GUIDE.md` for complete contract audit and handoff specifications for all teammates.
