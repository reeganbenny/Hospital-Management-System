# MediCare HMS – Hospital Management System

A full-stack hospital management system with role-based access for **patients**, **doctors**, and **admins**. Built with Flask (REST API), Vue 3, Celery, and Redis.

**DB diagram (v1):** https://dbdiagram.io/d/MedicareHMS-62177cf8485e4335430edbac

---

## Prerequisites

- **Node.js** (v18+) and **npm**
- **Python 3.10+**
- **Redis** (e.g. `brew install redis` on macOS)
- **Docker** (optional, for MailHog)

---

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` in `backend/` if needed (e.g. `FLASK_ENV=development`, `REDIS_URL=redis://localhost:6379/0`, database URL). The app can run with defaults (SQLite, port 5001).

### Frontend

```bash
cd frontend
npm install
```

---

## Running the application

Run these in separate terminals. Start **Redis** first, then **backend**, then **Celery** (if you use CSV export or scheduled reports), then **frontend**. Optionally start **MailHog** for local email testing.

### 1. Redis

```bash
brew services start redis
```

| Command | Action |
|--------|--------|
| `brew services start redis` | Start Redis |
| `brew services stop redis` | Stop Redis |
| `brew services restart redis` | Restart Redis |
| `brew services list` | List all Homebrew services and their status |

To stop Redis when done:

```bash
brew services stop redis
```

### 2. Backend (Flask API)

```bash
cd backend && source venv/bin/activate
python main.py
```

Runs at **http://localhost:5001** by default.

### 3. Celery (background jobs)

For patient CSV export and scheduled reports (e.g. monthly doctor reports):

**Option A – worker + beat in one process:**

```bash
cd backend
source venv/bin/activate
celery -A run_celery.celery worker -l info --beat
```

**Option B – worker and beat in two terminals:**

```bash
# Terminal 1: worker (runs tasks)
cd backend && source venv/bin/activate
celery -A run_celery.celery worker -l info

# Terminal 2: beat (triggers daily & monthly on schedule)
cd backend && source venv/bin/activate
celery -A run_celery.celery beat -l info
```

### 4. Frontend (Vite dev server)

```bash
cd frontend && npm run dev
```

Runs at **http://localhost:8080** (or the port Vite prints). The frontend proxies `/api` and `/static` to the backend.

### 5. MailHog (optional – local email testing)

To capture outgoing emails (e.g. monthly reports) locally:

```bash
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

- SMTP: `localhost:1025`
- Web UI: http://localhost:8025

Configure the backend to use this SMTP server when you want to test emails.

---

## Quick reference

| Service    | Command / URL |
|-----------|----------------|
| Frontend  | `cd frontend && npm run dev` → http://localhost:8080 |
| Backend   | `cd backend && source venv/bin/activate` then `python main.py` → http://localhost:5001 |
| Redis     | `brew services start redis` |
| Celery    | `celery -A run_celery.celery worker -l info --beat` (from `backend/` with venv active) |
| MailHog   | `docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog` → http://localhost:8025 |

API documentation is available in **`api.yaml`** (OpenAPI 3.0).
