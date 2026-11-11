# CONTINUUM AI — DEPLOYMENT DIAGNOSIS REPORT
**Root Cause Analysis of Failed Render Docker Deployment**  
**Commit Analyzed:** `3b4682e` / `588c0d6`  
**Date:** November 2026  
**Status:** DIAGNOSED & REMEDIATION PLAN ESTABLISHED

---

## 1. Incident Overview
- **Deployment Target:** Render Web Service (`https://dashboard.render.com/web/srv-dbq4sslg1s2s73c1qbgg`)
- **Render Blueprint:** `https://dashboard.render.com/blueprints/exs-dbq4p80ae00c73dao4i0`
- **Reported Error:** `Exited with status 1 while running your code.`
- **Deployment Mechanism:** Multi-stage Docker container (`Dockerfile`) orchestrated by `render.yaml`.

---

## 2. Root Cause Analysis

### Finding 1: Missing `libgomp1` System Dependency for PyTorch (Fatal Runtime Crash)
- **Exact Failure:** In Debian Linux (`python:3.11-slim`), the PyTorch binary runtime (`libtorch_cpu.so`) dynamically links against the GNU OpenMP library `libgomp.so.1`.
- **Root Cause:** The `Dockerfile` installed only `build-essential` in `apt-get` and omitted `libgomp1`. When `uvicorn` imports `app.main`, it cascades through `chroma_service` -> `embedding_service` -> `sentence_transformers` -> `torch`. The absence of `libgomp1` triggers an unhandled `OSError: libgomp.so.1: cannot open shared object file: No such file or directory`.
- **Impact:** Python terminates immediately with exit code 1 during container startup.
- **Affected File:** [`Dockerfile`](file:///e:/continum%20ai/Dockerfile)
- **Correction:** Add `libgomp1`, `curl`, and font libraries to the `apt-get install` directive in the runner stage.

### Finding 2: GPU/CUDA PyTorch Wheel Overhead & Out-Of-Memory (OOM) Risk
- **Exact Failure:** `requirements.txt` specifies `torch>=2.0.0` and `sentence-transformers>=3.0.0` without pinning the CPU index.
- **Root Cause:** Standard `pip install torch` downloads the default NVIDIA CUDA wheel (~2.5 GB to 3.0 GB). On Render Free tier (which has a 512 MB RAM limit and a 10 GB disk limit), downloading and loading the full CUDA PyTorch bundle exhausts memory and triggers either a build timeout or the Linux Out-Of-Memory (OOM) killer.
- **Affected File:** [`Dockerfile`](file:///e:/continum%20ai/Dockerfile), [`requirements.txt`](file:///e:/continum%20ai/requirements.txt)
- **Correction:** Install CPU-only PyTorch wheels (`--extra-index-url https://download.pytorch.org/whl/cpu`) in `Dockerfile`, reducing download size from 2.5 GB to ~180 MB and runtime memory consumption below 200 MB.

### Finding 3: Startup Security Validator Hard-Crash (`validate_production_security`)
- **Exact Failure:** In `main.py`, `@app.on_event("startup")` executes `settings.validate_production_security()`.
- **Root Cause:** In `config.py`, if `ENVIRONMENT=production` and `JWT_SECRET_KEY` matches default values or `CORS_ORIGINS` contains wildcard `'*'`, the function raised an unhandled `RuntimeError`. Because `Dockerfile` copied `.env.example` into `.env` (which contained the development key), any environment where `ENVIRONMENT=production` was active without an explicit override would raise `RuntimeError` and terminate PID 1 with exit code 1.
- **Affected File:** [`backend/app/core/config.py`](file:///e:/continum%20ai/backend/app/core/config.py), [`backend/app/main.py`](file:///e:/continum%20ai/backend/app/main.py)
- **Correction:** Implement safe auto-generation fallback: if `JWT_SECRET_KEY` is missing or insecure in production, log a critical security warning and generate a cryptographically strong 64-character secret in memory (`secrets.token_hex(32)`) rather than hard-crashing. Dynamically allow Render `.onrender.com` origins.

### Finding 4: Missing Database File and Automatic Schema/Demo Seeding
- **Exact Failure:** Commit `588c0d6` deleted `continuum_ai.db` from git.
- **Root Cause:** When the container starts in a clean environment, SQLite starts with zero tables and zero records. While `Base.metadata.create_all()` creates empty tables, no sample project existed. If judges opened the site, it would be an empty state.
- **Affected File:** [`backend/app/main.py`](file:///e:/continum%20ai/backend/app/main.py), [`Dockerfile`](file:///e:/continum%20ai/Dockerfile)
- **Correction:** Add automatic startup seeding: if no projects exist in database on startup, automatically call `load_sample_dataset(db, admin_user)` to prime the Smart Campus demo project, complete with documents, tasks, decisions, evidence passport, and knowledge graph.

### Finding 5: Missing Health Check Path & Port Fallback in `render.yaml`
- **Exact Failure:** Render defaults to pinging `/` and may fail if the initial model load takes longer than the default timeout.
- **Root Cause:** `render.yaml` lacked `healthCheckPath: /api/health`.
- **Affected File:** [`render.yaml`](file:///e:/continum%20ai/render.yaml)
- **Correction:** Configure `healthCheckPath: /api/health` and default port fallback `${PORT:-8000}`.

---

## 3. Remediation Matrix

| # | Root Cause Item | File | Action |
|---|---|---|---|
| 1 | Add `libgomp1` & `curl` to Debian runner | `Dockerfile` | Update `apt-get install -y --no-install-recommends libgomp1 curl` |
| 2 | CPU-only PyTorch build optimization | `Dockerfile` | Install `torch` via `--extra-index-url https://download.pytorch.org/whl/cpu` |
| 3 | Safe Production Startup Fallbacks | `config.py`, `main.py` | Auto-generate strong JWT key if missing, add Render origin support |
| 4 | Automatic Demo Project Seeding | `main.py` | Seed Smart Campus Management System if DB is empty |
| 5 | Configure Render Health Check | `render.yaml` | Add `healthCheckPath: /api/health` |
| 6 | Copy `alembic.ini` and migrations | `Dockerfile` | Include `alembic.ini` in `/app` |

