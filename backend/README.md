# DayFlow Backend – Stage 5: Secure Multi-User Deployment

DayFlow backend is built with **FastAPI**, **SQLAlchemy 2**, **Alembic**, and **Pydantic v2**.

## Features in Stage 5
- User registration, login, logout with JWT Bearer tokens (`/auth/*`)
- Secure password hashing with `bcrypt` (salted, constant-time verification)
- Enforced user-level data ownership across every endpoint (`/tasks/*` and `/analytics`)
- Supabase free PostgreSQL tier compatibility
- Render deployment readiness (`render.yaml`, environment variables)
- Alembic database migration with backward compatibility and zero data loss

## Quickstart

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Running Tests

```powershell
.\venv\Scripts\python -m pytest
```

All 48 tests pass:
- `tests/test_health.py` (1 test)
- `tests/test_stage3.py` (6 tests)
- `tests/test_stage4.py` (4 tests)
- `tests/test_stage5.py` (11 tests)
- `tests/test_tasks.py` (26 tests)
