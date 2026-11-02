# DayFlow

> A production-quality, multi-user personal productivity and finance management platform.

DayFlow unites daily planning, task execution, budget tracking, and financial analytics into a cohesive, high-performance web platform.

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (REST API)
- **Data Modeling & Validation**: [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **ORM & Database Toolkit**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database Driver**: [psycopg 3](https://www.psycopg.org/psycopg3/)
- **Database Engine**: PostgreSQL 18
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Testing**: [Pytest](https://docs.pytest.org/) & HTTPX (`TestClient`)

### Frontend
- **Framework**: [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Routing**: [React Router v7](https://reactrouter.com/)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Code Quality**: ESLint 9

---

## Project Structure

```
DayFlow/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/v1/           # API routes & endpoints
│   │   ├── core/             # Settings, logging, and security
│   │   ├── db/               # SQLAlchemy engine & session factory
│   │   ├── models/           # Declarative database models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business domain logic
│   │   ├── repositories/     # Data access patterns
│   │   └── main.py           # Application entrypoint & middleware
│   ├── tests/                # Pytest suite with isolated test DB
│   ├── alembic/              # Database migration scripts
│   ├── alembic.ini           # Alembic config
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Backend environment template
│
├── frontend/                 # React + Vite Application
│   ├── src/
│   │   ├── api/              # Axios client and endpoint functions
│   │   ├── assets/           # Static media
│   │   ├── components/       # Reusable components
│   │   ├── hooks/            # Custom hooks
│   │   ├── layouts/          # Page layouts
│   │   ├── pages/            # View pages
│   │   ├── routes/           # Routing configuration
│   │   ├── types/            # TypeScript interfaces
│   │   ├── utils/            # Shared utilities
│   │   ├── App.tsx           # Main application component
│   │   └── main.tsx          # React DOM entry
│   ├── public/               # Public assets
│   ├── package.json          # Frontend scripts & dependencies
│   └── .env.example          # Frontend environment template
│
├── docs/                     # Architectural and Setup Documentation
│   ├── architecture.md
│   └── development-setup.md
│
├── .gitignore
└── README.md
```

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 18

### 2. Database
Create your PostgreSQL database:
```sql
CREATE DATABASE dayflow_db;
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run tests
pytest

# Start backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend endpoints:
- Root API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health Liveness: [http://127.0.0.1:8000/api/v1/health/live](http://127.0.0.1:8000/api/v1/health/live)
- Health Readiness: [http://127.0.0.1:8000/api/v1/health/ready](http://127.0.0.1:8000/api/v1/health/ready)
- Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env

# Start frontend development server
npm run dev
```

Frontend application will open at [http://localhost:5173](http://localhost:5173).

---

## Documentation
- Detailed architectural guidelines: [`docs/architecture.md`](docs/architecture.md)
- Development setup walkthrough: [`docs/development-setup.md`](docs/development-setup.md)

