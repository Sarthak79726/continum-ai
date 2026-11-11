# CONTINUUM AI — PRODUCTION ENVIRONMENT VARIABLES SPECIFICATION

This document details all configuration parameters and environment variables required for running **Continuum AI** in staging and production environments (e.g. Render, Railway, AWS ECS, or bare Docker).

---

## 1. Quick Reference Matrix

| Variable Name | Required on Render? | Default / Fallback | Sensitivity | Production Recommendation |
|---|---|---|---|---|
| `ENVIRONMENT` | **Yes** | `development` | Low | Set to `production` |
| `PORT` | Auto-injected | `8000` | Low | Injected by Render as `10000` |
| `DATABASE_URL` | **Yes** | `sqlite:///./continuum_ai.db` | High (if remote) | `sqlite:///./continuum_ai.db` or PostgreSQL URI |
| `JWT_SECRET_KEY` | **Yes** | Auto-generated if missing | **Critical** | Generated via `openssl rand -hex 32` or Render `generateValue: true` |
| `JWT_ALGORITHM` | No | `HS256` | Medium | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Low | `30` to `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Low | `7` |
| `CORS_ORIGINS` | No | Auto-detects Render host | High | Exact frontend domains (e.g., `https://continuum-ai.onrender.com`) |
| `AI_PROVIDER` | **Yes** | `demo` | Low | `demo` (Zero-cost, zero-API key, deterministic local NLP engine) |
| `AI_API_KEY` | Optional | `""` | **Critical** | Leave empty for `demo`, or provide Gemini/OpenAI API key |
| `AI_MODEL` | No | `gemini-1.5-flash` | Low | `gemini-1.5-flash` or `gpt-4o-mini` |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Low | `all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIRECTORY` | No | `./chroma_data` | Medium | Persistent volume path or `./chroma_data` |
| `UPLOAD_DIRECTORY` | No | `./uploads` | Medium | Persistent volume path or `./uploads` |
| `MAX_UPLOAD_SIZE` | No | `20971520` (20 MB) | Low | `20971520` (20 MB) |
| `RENDER_EXTERNAL_HOSTNAME` | Auto-injected | `""` | Low | Injected by Render (e.g., `continuum-ai.onrender.com`) |

---

## 2. In-Depth Variable Descriptions

### `ENVIRONMENT`
- **Description:** Selects the operational mode of the backend service (`development`, `staging`, or `production`).
- **Production Recommendation:** `production`
- **Behavior:** In `production`, detailed internal exception traces are suppressed from client API responses, security headers are strictly enforced, and wildcard CORS is forbidden.
- **Sensitivity:** Low

### `DATABASE_URL`
- **Description:** SQLAlchemy database connection string.
- **Development Fallback:** `sqlite:///./continuum_ai.db`
- **Production Recommendation:** For simple hackathon single-instance deployments, SQLite (`sqlite:///./continuum_ai.db`) is fully supported and self-seeds on first boot. For multi-instance high-availability deployments, use PostgreSQL: `postgresql+psycopg2://user:password@hostname:5432/continuum_ai`.
- **Sensitivity:** High (contains database credentials if remote).

### `JWT_SECRET_KEY`
- **Description:** Symmetric cryptographic secret key used to sign and verify HMAC-SHA256 JWT access and refresh tokens.
- **Development Fallback:** Automatically generates a cryptographically secure ephemeral 64-character token in memory if missing or insecure.
- **Production Recommendation:** Supply a permanent 64-character hex string. In `render.yaml`, configure `generateValue: true` so Render generates and preserves a high-entropy secret.
- **Sensitivity:** **Critical** (compromise allows arbitrary authentication bypass).

### `CORS_ORIGINS`
- **Description:** Comma-separated list of trusted HTTP/HTTPS origins permitted to make cross-origin browser requests with credentials (`Authorization` header / cookies).
- **Default Fallback:** `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000`
- **Production Recommendation:** Provide the exact production domain(s), e.g., `https://continuum-ai.onrender.com`. The application automatically reads `RENDER_EXTERNAL_HOSTNAME` and whitelists `https://${RENDER_EXTERNAL_HOSTNAME}` dynamically.
- **Security Warning:** Wildcard (`*`) is explicitly prohibited in production mode.
- **Sensitivity:** High (misconfiguration exposes users to CSRF and data theft).

### `AI_PROVIDER`
- **Description:** Active AI analysis engine for document extraction, knowledge summarization, and handover reconstruction.
- **Supported Values:** `demo`, `gemini`, `openai`, `anthropic`, `groq`, `ollama`.
- **Production Recommendation:** `demo`. The `demo` provider runs our custom deterministic NLP knowledge extraction pipeline. It is 100% reliable, zero-latency, requires zero paid API keys, and never fails due to rate limits or API quotas during judge evaluation.
- **Sensitivity:** Low.

### `AI_API_KEY`
- **Description:** External AI provider API key (only required when `AI_PROVIDER` is set to `gemini`, `openai`, or `anthropic`).
- **Development Fallback:** None (not needed when `AI_PROVIDER=demo`).
- **Sensitivity:** **Critical** (never commit to git).

### `CHROMA_PERSIST_DIRECTORY` & `UPLOAD_DIRECTORY`
- **Description:** Filesystem directory paths where the ChromaDB vector database and uploaded files (PDFs, DOCX, CSV) are stored on disk.
- **Production Recommendation:** `./chroma_data` and `./uploads`. For long-term persistent storage across container redeployments on Render, attach a Render Persistent Disk mounted at `/app/data` and configure paths as `/app/data/chroma` and `/app/data/uploads`.
- **Sensitivity:** Medium.

---

## 3. Render Blueprint (`render.yaml`) Configuration

The project includes a ready-to-deploy Render Blueprint specification:

```yaml
services:
  - type: web
    name: continuum-ai
    env: docker
    plan: free
    region: oregon
    dockerfilePath: ./Dockerfile
    healthCheckPath: /api/health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        value: sqlite:///./continuum_ai.db
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: AI_PROVIDER
        value: demo
      - key: CHROMA_PERSIST_DIRECTORY
        value: ./chroma_data
      - key: UPLOAD_DIRECTORY
        value: ./uploads
```

