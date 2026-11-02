# DayFlow Architecture Documentation

## 1. Overview & System Design

DayFlow is designed as a modular, production-ready full-stack application following clean architecture and separation of concerns.

The application is structured as a monorepo consisting of:
- **`backend/`**: A high-performance Python 3.11+ REST API built with FastAPI, SQLAlchemy 2.0, Pydantic v2, and PostgreSQL (psycopg 3).
- **`frontend/`**: A modern React 18 single-page application built with TypeScript, Vite, Tailwind CSS, React Router, and Axios.
- **`docs/`**: Architecture, design specifications, and development setup guides.

---

## 2. Backend Architecture (`backend/`)

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── health.py          # Health probe endpoints (live/ready)
│   │       ├── router.py              # Centralized v1 API router
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings & environment config
│   │   └── __init__.py
│   ├── db/
│   │   ├── session.py                 # SQLAlchemy 2.0 engine, Base, & session dependency
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py                # Declarative SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── health.py                  # Pydantic v2 request/response schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── health_service.py          # Encapsulated business/service logic
│   │   └── __init__.py
│   ├── repositories/
│   │   └── __init__.py                # Data access layer (abstracts SQL queries)
│   └── main.py                        # FastAPI application initialization & middleware
├── tests/
│   ├── conftest.py                    # Pytest fixtures and in-memory test database
│   └── test_health.py                 # Health and root endpoint unit tests
├── alembic/                           # Database schema migration files
│   ├── versions/
│   ├── env.py                         # Alembic migration environment
│   └── script.py.mako
├── alembic.ini                        # Alembic configuration file
├── requirements.txt                   # Backend dependencies
├── .env.example                       # Template for environment configuration
└── .env                               # Local backend configuration (ignored by git)
```

### Directory Responsibilities

- **`app/api/v1/`**: Routing layer. Routes requests, validates HTTP parameters via schemas, calls services, and formats HTTP responses. Strictly avoids direct database queries or raw business logic.
- **`app/core/`**: Central application configurations (`Settings` using `pydantic-settings`), logging configuration, security constants, and shared utilities.
- **`app/db/`**: Database engine setup, declarative base definition, connection pool configuration, and the `get_db` FastAPI dependency for request-scoped database sessions.
- **`app/models/`**: SQLAlchemy 2.0 declarative models representing PostgreSQL tables and relational mappings.
- **`app/schemas/`**: Pydantic v2 models for request validation and response serialization.
- **`app/services/`**: Domain business logic. Services coordinate actions, domain rules, and data manipulation between repositories and API endpoints.
- **`app/repositories/`**: Clean abstraction over the ORM and SQL queries for each domain entity.
- **`alembic/`**: Controlled database migrations tracking schema changes over time.

---

## 3. Frontend Architecture (`frontend/`)

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts                  # Configured Axios instance with interceptors
│   │   └── health.ts                  # Health & system status API calls
│   ├── assets/                        # Static assets (images, icons, svgs)
│   ├── components/                    # Reusable UI components
│   ├── hooks/
│   │   └── useHealthCheck.ts          # Custom React hooks (health probe polling)
│   ├── layouts/                       # Layout containers (e.g. Nav, Sidebar)
│   ├── pages/
│   │   └── WelcomePage.tsx            # Initial foundation landing page
│   ├── routes/
│   │   └── index.tsx                  # React Router configuration
│   ├── types/
│   │   └── api.ts                     # TypeScript interfaces and API response types
│   ├── utils/                         # Frontend utility functions
│   ├── App.tsx                        # Root React component
│   ├── main.tsx                       # React DOM entry point
│   └── index.css                      # Tailwind CSS entry directives
├── public/                            # Static public files
├── index.html                         # Single-page HTML document
├── vite.config.ts                     # Vite bundler configuration & path aliases
├── tailwind.config.js                 # Tailwind CSS theme configuration
├── postcss.config.js                  # PostCSS plugins
├── tsconfig.json                      # TypeScript strict compiler options
└── package.json                       # Frontend dependencies and npm scripts
```

### Frontend Design Highlights

- **Typed API Layer**: Axios is encapsulated inside `src/api/client.ts` with error handling interceptors. Endpoints are grouped by domain with explicit TypeScript models.
- **Custom Hooks**: Business state and asynchronous fetching logic are kept clean and testable inside `src/hooks/`.
- **Responsive & Modern Styling**: Tailwind CSS utilities combined with custom design tokens ensure a sleek dark-mode aesthetic with accessible status indicators.

---

## 4. API Endpoints Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root information, application name, and version |
| `GET` | `/api/v1/health/live` | Application liveness probe (returns `200 OK`) |
| `GET` | `/api/v1/health/ready` | Dependency & database readiness check (`SELECT 1`). Returns `200 OK` when healthy, or `503 Service Unavailable` if database is down |
| `GET` | `/docs` | Interactive Swagger API documentation |
| `GET` | `/redoc` | OpenAPI ReDoc documentation |

