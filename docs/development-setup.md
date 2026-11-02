# DayFlow — Local Development Setup Guide

This guide walks you through setting up DayFlow locally on your development workstation.

---

## Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.11+** (`python --version`)
- **Node.js 18+** / **npm 9+** (`node --version`, `npm --version`)
- **PostgreSQL 18** (or locally running PostgreSQL instance)
- **Git**

---

## 1. PostgreSQL Database Setup

1. Open PostgreSQL CLI (`psql`) or pgAdmin:
   ```bash
   psql -U postgres
   ```
2. Create the DayFlow database:
   ```sql
   CREATE DATABASE dayflow_db;
   ```
3. Verify connection to the newly created database:
   ```sql
   \c dayflow_db
   ```

---

## 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # On Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # On Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Adjust `DATABASE_URL` with your local PostgreSQL credentials:
     ```env
     DATABASE_URL="postgresql+psycopg://postgres:<your_password>@localhost:5432/dayflow_db"
     ```
5. Run tests:
   ```bash
   pytest
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000) and Swagger docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure the environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Verify `VITE_API_BASE_URL` points to your backend instance:
     ```env
     VITE_API_BASE_URL="http://localhost:8000"
     ```
4. Build or typecheck:
   ```bash
   npm run build
   ```
5. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser at [http://localhost:5173](http://localhost:5173).

