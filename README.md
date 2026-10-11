# DayFlow – Stage 1: Backend API

DayFlow is a personal task management application. This document covers
**Stage 1**: the FastAPI backend only. The React frontend will be added in a
later stage.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project structure](#project-structure)
3. [Environment setup](#environment-setup)
4. [Dependency installation](#dependency-installation)
5. [Environment configuration](#environment-configuration)
6. [Database migrations](#database-migrations)
7. [Running the API](#running-the-api)
8. [Swagger UI](#swagger-ui)
9. [Running tests](#running-tests)
10. [API reference](#api-reference)

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| pip | 23 + |

---

## Project structure

```
dayflow/
└── backend/
    ├── app/
    │   ├── __init__.py
    │   ├── config.py       # Pydantic-settings config (reads .env)
    │   ├── database.py     # SQLAlchemy 2 engine + session factory
    │   ├── models.py       # ORM models: Task, TaskEvent
    │   ├── schemas.py      # Pydantic request/response schemas
    │   ├── crud.py         # Database CRUD operations
    │   ├── main.py         # FastAPI app + CORS + router registration
    │   └── routers/
    │       ├── __init__.py
    │       └── tasks.py    # /tasks endpoints
    ├── alembic/
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/       # Auto-generated migration scripts
    ├── tests/
    │   ├── conftest.py     # Fixtures (isolated test DB, TestClient)
    │   ├── test_health.py
    │   └── test_tasks.py
    ├── data/               # SQLite database files (git-ignored)
    ├── venv/               # Virtual environment (git-ignored)
    ├── alembic.ini
    ├── pyproject.toml      # pytest config
    ├── requirements.txt
    ├── .env                # Local secrets (git-ignored; copy from .env.example)
    └── .env.example
```

---

## Environment setup

All commands below should be run from the **`backend/`** directory.

### Create the virtual environment

```powershell
# PowerShell
python -m venv venv
```

### Activate the virtual environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

> If you see an execution-policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Command Prompt (cmd.exe):**
```cmd
venv\Scripts\activate.bat
```

**Git Bash / WSL:**
```bash
source venv/Scripts/activate
```

You should see `(venv)` in your prompt when the environment is active.

---

## Dependency installation

```powershell
pip install -r requirements.txt
```

---

## Environment configuration

Copy the example file and edit it:

```powershell
copy .env.example .env
```

Open `.env` and set:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./data/dayflow.db` | SQLite path (use an absolute path on Render: `sqlite:////mnt/data/dayflow.db`) |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated list of React dev server origins |
| `APP_ENV` | `development` | `development` or `production` |

> **Never commit `.env`** – it is listed in `.gitignore`.

---

## Database migrations

Alembic manages all schema changes. Run these commands from `backend/`:

```powershell
# Apply all pending migrations (creates the DB file if it does not exist)
.\venv\Scripts\alembic.exe upgrade head

# Check current migration status
.\venv\Scripts\alembic.exe current

# Create a new migration after editing models.py
.\venv\Scripts\alembic.exe revision --autogenerate -m "describe your change"
```

> `render_as_batch=True` is enabled in `alembic/env.py` so SQLite `ALTER TABLE`
> operations work correctly.

---

## Running the API

```powershell
# Development server with hot-reload
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

## Swagger UI

Open your browser at:

```
http://localhost:8000/docs
```

ReDoc is also available at `http://localhost:8000/redoc`.

---

## Running tests

Tests use a temporary SQLite file isolated from your development database.

```powershell
# Run all tests with verbose output
.\venv\Scripts\pytest.exe -v

# Run a specific test file
.\venv\Scripts\pytest.exe tests/test_tasks.py -v

# Run a specific test
.\venv\Scripts\pytest.exe tests/test_tasks.py::TestCreateTask::test_create_valid -v

# Show coverage (if pytest-cov is installed)
.\venv\Scripts\pytest.exe --cov=app --cov-report=term-missing
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/tasks` | Create a task |
| `GET` | `/tasks` | List tasks (excludes deleted) |
| `GET` | `/tasks/{id}` | Get task by ID |
| `PUT` | `/tasks/{id}` | Update a task |
| `PATCH` | `/tasks/{id}/complete` | Mark task as completed |
| `DELETE` | `/tasks/{id}` | Soft-delete a task |

### Query parameters for `GET /tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | int | Records to skip (default: 0) |
| `limit` | int | Max records (default: 100, max: 500) |
| `status` | string | Filter by `pending` or `completed` |
| `category` | string | Filter by category |
| `priority` | string | Filter by `low`, `medium`, or `high` |

### Task fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | ✅ | 1–255 characters |
| `description` | string | – | Optional long text |
| `scheduled_date` | date | ✅ | Local date (Asia/Kolkata) |
| `start_time` | time | – | Local time (must be before `end_time`) |
| `end_time` | time | – | Local time |
| `priority` | enum | – | `low` / `medium` / `high` (default: `medium`) |
| `category` | enum | – | `work` / `personal` / `learning` / `health` / `other` (default: `other`) |
| `status` | enum | – | `pending` / `completed` (read-only on create) |

---

## Notes for production (Render)

1. Set `DATABASE_URL=sqlite:////mnt/data/dayflow.db` (four slashes = absolute path).
2. Mount a persistent disk at `/mnt/data` in the Render service settings.
3. Set `APP_ENV=production`.
4. Set `ALLOWED_ORIGINS` to your production React origin.
5. Run `alembic upgrade head` in the Render build or start command.
