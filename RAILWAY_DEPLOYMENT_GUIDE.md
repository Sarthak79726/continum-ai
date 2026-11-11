# CONTINUUM AI — RAILWAY PRODUCTION DEPLOYMENT GUIDE

**Target Platform:** Railway ([railway.com](https://railway.com))  
**Repository:** `https://github.com/Sarthak79726/continum-ai`  
**Deployment Architecture:** Unified Full-Stack Container (React 19 Vite SPA + Python 3.11 FastAPI Backend)  

---

## 1. Architecture & Port Binding Verification

Continuum AI deploys to Railway as a **Single Unified Web Service**:
- **Port Binding:** Railway automatically injects the `$PORT` environment variable. The server command binds to `0.0.0.0:${PORT:-8000}`, guaranteeing Railway's proxy can route traffic.
- **Unified Delivery:** FastAPI serves both the REST API endpoints (`/api/*`) and the static React SPA (`/*` with client-side routing fallback), completely eliminating cross-origin CORS barriers in production.
- **Frontend API Base:** The React client (`frontend/src/services/api.ts`) communicates via relative path `/api`, meaning zero hardcoded localhost or domain configuration is required.
- **Health Checks:** Configured for `/api/health` and `/health` with a 300-second startup grace period.

```mermaid
flowchart LR
    User[Judge / Browser] -->|Port 80/443| Edge[Railway Edge Proxy]
    Edge -->|PORT (Dynamic)| Container[Unified Continuum AI Container]
    
    subgraph Container
        FastAPI[FastAPI Application] -->|/api/*| Routers[API Routers]
        FastAPI -->|/*| SPA[React 19 Vite SPA]
        FastAPI -->|/api/health| HealthCheck[Health Check]
        Routers --> DB[(SQLite - continuum_ai.db)]
        Routers --> Chroma[(ChromaDB Vector Store)]
        Routers --> LocalNLP[Deterministic Extraction Engine]
    end
```

---

## 2. Railway Deployment Configuration Files

### `railway.json`
Created in repository root:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --app-dir ./backend --host 0.0.0.0 --port ${PORT:-8000}",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 3. Persistent Storage on Railway (Volumes)

Railway containers have an ephemeral filesystem by default. To preserve user documents, ChromaDB vector collections, and SQLite database records across deployments:

1. In Railway Dashboard, navigate to your **Continuum AI** service.
2. Go to **Settings** ➔ **Volumes** ➔ Click **+ Add Volume**.
3. Set the **Mount Path** to:
   ```
   /data
   ```
4. In the service **Variables**, add:
   ```env
   RAILWAY_VOLUME_MOUNT_PATH=/data
   ```
   *The application automatically relocates `continuum_ai.db`, `./chroma_data`, and `./uploads` to `/data/`.*

*(Note: Even without a persistent volume, the application automatically boots and self-seeds the demonstration Smart Campus dataset into memory/container storage on every deployment).*

---

## 4. Required Railway Environment Variables

Configure these variables under the **Variables** tab of your Railway service:

| Variable Name | Recommended Production Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Enforces production security headers and error redaction |
| `DATABASE_URL` | `sqlite:///./continuum_ai.db` | Default path (or `sqlite:////data/continuum_ai.db` with volume) |
| `JWT_SECRET_KEY` | *(Click "Generate" or use a 64-char hex string)* | Cryptographic key for JWT session validation |
| `AI_PROVIDER` | `demo` | Deterministic local extraction engine (zero cost, zero external API key) |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_data` | Vector database storage path |
| `UPLOAD_DIRECTORY` | `./uploads` | Uploaded document storage path |

---

## 5. Step-by-Step Deployment Instructions

### Step 1: Push Code to GitHub
All deployment files (`railway.json`, updated `Dockerfile`, `config.py`, `main.py`) are pushed to `main`:
```bash
git push origin main
```

### Step 2: Create Railway Project
1. Go to [railway.com](https://railway.com) and log in.
2. Click **New Project** ➔ **Deploy from GitHub repo**.
3. Select `Sarthak79726/continum-ai`.
4. Railway will automatically detect `Dockerfile` and `railway.json`.

### Step 3: Configure Environment Variables
1. Click on the newly created service tile.
2. Navigate to the **Variables** tab.
3. Click **RAW Editor** and paste:
   ```env
   ENVIRONMENT=production
   DATABASE_URL=sqlite:///./continuum_ai.db
   AI_PROVIDER=demo
   CHROMA_PERSIST_DIRECTORY=./chroma_data
   UPLOAD_DIRECTORY=./uploads
   ```
4. Add `JWT_SECRET_KEY` by generating a random string (e.g. `openssl rand -hex 32`).

### Step 4: Generate Public Domain
1. In the service **Settings** tab, scroll to **Networking**.
2. Click **Generate Domain** under the Public Networking section.
3. Railway will assign an official public domain, for example:
   ```
   https://continum-ai-production.up.railway.app
   ```

### Step 5: Verify Deployment
Once Railway reports **Success** and the health check returns `healthy`, open the URL:
- Frontend: `https://<your-service>.up.railway.app`
- API Health: `https://<your-service>.up.railway.app/api/health`
- Swagger Docs: `https://<your-service>.up.railway.app/docs`

---

## 6. Judge / Evaluator Credentials
- **Email:** `demo@continuum.ai`
- **Password:** `password123`
- **Role:** `ADMIN`
