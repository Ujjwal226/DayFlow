# DayFlow – Secure Multi-User Personal Task Management

DayFlow is a modern, high-performance personal task management application built with **FastAPI**, **SQLAlchemy 2**, **Alembic**, and **React 19** with **Vite** and **Tailwind CSS v4**.

**Stage 5** introduces **Secure Multi-User Deployment**:
- User registration, login, logout with JWT Bearer tokens
- Secure bcrypt password hashing with unique salts
- Strict cross-user data isolation across all tasks, scheduling, calendar, history, and analytics endpoints
- Production support for Supabase's free PostgreSQL tier
- Safe database migration preserving existing task history
- Free-tier Render deployment configuration (`render.yaml`)

---

## Table of Contents

1. [Architecture & Tech Stack](#architecture--tech-stack)
2. [Security & Privacy Design](#security--privacy-design)
3. [Local Development Setup](#local-development-setup)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
4. [Database Migrations & Data Safety](#database-migrations--data-safety)
5. [Free-Tier Deployment Guide (Supabase + Render)](#free-tier-deployment-guide-supabase--render)
   - [1. Supabase PostgreSQL Setup](#1-supabase-postgresql-setup)
   - [2. Render Deployment Setup](#2-render-deployment-setup)
6. [API Reference](#api-reference)
7. [Running Tests & Actual Results](#running-tests--actual-results)

---

## Architecture & Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React, Recharts, Sonner |
| **Backend** | FastAPI, Python 3.11, Pydantic v2, Pydantic-Settings |
| **Database** | SQLite (local dev), PostgreSQL (Supabase free-tier in production) |
| **ORM & Migrations**| SQLAlchemy 2.0 (Mapped columns), Alembic |
| **Authentication** | PyJWT (HS256 Bearer tokens), bcrypt password hashing |
| **Deployment** | Render (Free Tier Web Service + Static Site), Supabase (Free Tier PostgreSQL) |

---

## Security & Privacy Design

1. **Authentication**:
   - `POST /auth/register`: Validates email format and password length (minimum 6 characters), hashes password with `bcrypt`, creates the user, and issues a JWT token. Duplicate emails are safely rejected.
   - `POST /auth/login`: Verifies plaintext password against stored bcrypt hash using constant-time comparison, and returns a signed JWT access token.
   - `GET /auth/me`: Validates JWT token and returns current user profile.
   - `POST /auth/logout`: Invalidates client session.

2. **Data Ownership & Isolation**:
   - Every task record is tied to a `user_id` foreign key.
   - All task queries (`GET /tasks`, `GET /tasks/history/date/{date}`, `GET /tasks/{id}`) filter strictly by `user_id == current_user.id`.
   - Modifying or deleting another user's task returns `404 Not Found`, preventing existence enumeration attacks.
   - Analytics computations (`GET /analytics`) and productivity heatmaps only compute statistics for tasks owned by the authenticated user.
   - Unauthenticated requests to any task or analytics endpoint immediately return `401 Unauthorized`.

3. **Safe Migration of Legacy Data**:
   - Alembic migration `c7e2b3a1d4f6_add_users_and_ownership.py` automatically preserves all pre-existing tasks and history.
   - If pre-existing tasks exist in the database, they are assigned to a legacy owner account whose email and password you supply via the `DEFAULT_USER_EMAIL` and `DEFAULT_USER_PASSWORD` environment variables **before running `alembic upgrade head`**. No hardcoded fallback credentials exist.
   - New user registrations receive a clean, completely private task space with zero cross-user exposure.

---

## Local Development Setup

### Backend Setup

1. **Navigate to the backend directory:**
   ```powershell
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```powershell
   # Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.example` to `.env`:
   ```powershell
   cp .env.example .env
   ```
   Default `.env` values for local development:
   ```env
   DATABASE_URL=sqlite:///./data/dayflow.db
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
   APP_ENV=development
   SECRET_KEY=development-secret-key-32chars-min-change-in-prod
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=10080
   ```

5. **Apply database migrations:**
   ```powershell
   alembic upgrade head
   ```

6. **Start the FastAPI dev server:**
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   Interactive Swagger documentation will be available at `http://localhost:8000/docs`.

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install npm dependencies:**
   ```powershell
   npm install
   ```

3. **Configure environment variables:**
   Ensure `frontend/.env` points to the local backend:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Start the Vite dev server:**
   ```powershell
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Database Migrations & Data Safety

The database schema is managed with Alembic:

- **Apply all migrations:**
  ```powershell
  alembic upgrade head
  ```
- **Revert to previous revision:**
  ```powershell
  alembic downgrade -1
  ```
- **Check current revision:**
  ```powershell
  alembic current
  ```

*Migration safety guarantee:* Existing data is never dropped or reset. Migrations use batch alter operations for SQLite compatibility and standard DDL for PostgreSQL.

---

## Free-Tier Deployment Guide (Supabase + Render)

### 1. Supabase PostgreSQL Setup

Supabase offers a free PostgreSQL tier that integrates seamlessly with DayFlow.

1. Sign up for free at [supabase.com](https://supabase.com) and click **New project**.
2. Set a project name (e.g. `dayflow-db`) and generate a strong database password.
3. Choose a region near your Render deployment (e.g., `East US` or `West US`).
4. Once the project is provisioned, go to **Project Settings** > **Database** > **Connection parameters**.
5. Copy the **Connection Pooling URL** (port 6543, Transaction mode):
   ```
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
   *(Note: DayFlow automatically converts any `postgres://` prefix to `postgresql://` for SQLAlchemy 2 compatibility).*

### 2. Render Deployment Setup

Deploy both the backend web service and the frontend static site on Render's free tier.

#### Method A: Using Render Blueprint (`render.yaml`)

1. Push your repository to GitHub.
2. Log in to [render.com](https://render.com) and click **New** > **Blueprint**.
3. Connect your GitHub repository.
4. Render will parse `render.yaml` and configure both services:
   - `dayflow-backend` (Python Web Service)
   - `dayflow-frontend` (Static Site)
5. Under environment variables for `dayflow-backend`, paste your Supabase `DATABASE_URL`.
6. Click **Apply**.

#### Method B: Manual Configuration on Render

**Backend (Web Service):**
- **Environment:** Python
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`
- **Environment Variables:**
  - `DATABASE_URL`: Your Supabase connection string
  - `ALLOWED_ORIGINS`: `https://<your-frontend-subdomain>.onrender.com`
  - `APP_ENV`: `production`
  - `SECRET_KEY`: A secure 32+ character random string
  - `ALGORITHM`: `HS256`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: `10080`

**Frontend (Static Site):**
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`
- **Rewrite Rules:** `/*` -> `/index.html` (Status: 200 Rewrite)
- **Environment Variables:**
  - `VITE_API_BASE_URL`: `https://<your-backend-subdomain>.onrender.com`

---

## API Reference

### Authentication (`/auth`)
- `POST /auth/register` – Register a new account (`email`, `password`, optional `full_name`)
- `POST /auth/login` – Login with email & password, returns JWT token & user info
- `GET /auth/me` – Retrieve authenticated user profile (`Bearer <token>` required)
- `POST /auth/logout` – Terminate user session

### Tasks (`/tasks`) – All endpoints require Bearer Token
- `POST /tasks` – Create a new task (automatically scoped to `user_id`)
- `GET /tasks` – List active tasks with pagination and status/category/priority filters
- `GET /tasks/{task_id}` – Retrieve task details (ownership verified; 404 if not owned)
- `PUT /tasks/{task_id}` – Update task title, description, category, or priority
- `PATCH /tasks/{task_id}/complete` – Mark task completed
- `PATCH /tasks/{task_id}/reopen` – Reopen completed task
- `PATCH /tasks/{task_id}/reschedule` – Reschedule date and optional start/end times
- `DELETE /tasks/{task_id}` – Soft-delete task
- `GET /tasks/history/date/{target_date}` – Retrieve tasks scheduled or originally scheduled on date
- `GET /tasks/{task_id}/history` – Retrieve audit event log for task

### Analytics (`/analytics`) – Requires Bearer Token
- `GET /analytics?days=84` – Comprehensive productivity metrics, daily counts, 7-day trend, and heatmap for the authenticated user

### Health (`/health`)
- `GET /health` – Unauthenticated uptime health check returning `{"status": "ok", "version": "0.1.0"}`

---

## Running Tests & Actual Results

### Automated Backend Test Suite

Run all tests from the `backend/` directory using the virtual environment:

```powershell
cd backend
.\venv\Scripts\python -m pytest
```

### Actual Test Results (Verified)

```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Projects\DayFlow\backend
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.7.0, asyncio-0.24.0
collected 48 items

tests\test_health.py .                                                   [  2%]
tests\test_stage3.py ......                                              [ 14%]
tests\test_stage4.py ....                                                [ 22%]
tests\test_stage5.py ...........                                         [ 45%]
tests\test_tasks.py ..........................                           [100%]

============================= 48 passed in 9.88s ==============================
```

### Summary of Stage 5 Verification
- **User Registration**: Verified valid registration, password length validation, duplicate email rejection (case-insensitive).
- **User Login**: Verified valid login with JWT issuance, invalid password rejection (401), nonexistent email rejection (401).
- **Password Security**: Verified passwords in database are hashed with bcrypt (`$2b$`) and match `bcrypt.checkpw`.
- **Unauthorized Access**: Verified all endpoints (`/tasks`, `/analytics`, `/auth/me`) return `401 Unauthorized` without a token or with an invalid token.
- **Cross-User Data Isolation**: Verified User B cannot list, retrieve, update, complete, reopen, reschedule, view history of, or delete User A's tasks (all return `404 Not Found`).
- **Analytics Isolation**: Verified User B's metrics, heatmap, and counts are completely isolated and independent of User A's activity.
- **Frontend Build**: Verified TypeScript compiler and Vite production bundle build with zero errors.
