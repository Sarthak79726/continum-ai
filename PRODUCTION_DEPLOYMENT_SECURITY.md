# CONTINUUM AI — PRODUCTION DEPLOYMENT & DEVSECOPS SECURITY GUIDE
**Platform Hardening, Container Security & Infrastructure Blueprint**  
**Version:** 2.1.0  
**Classification:** DevSecOps / Production Operations

---

## 1. Production Security Pre-Flight Checklist

Before deploying Continuum AI to production (Render, AWS, GCP, Railway, or on-premise Kubernetes), verify every item in this checklist:

- [x] **`ENVIRONMENT=production`** is set in environment variables.
- [x] **`JWT_SECRET_KEY`** is replaced with a cryptographically secure 64-character random key (`openssl rand -hex 32`).
- [x] **`CORS_ORIGINS`** strictly lists your actual production domain(s) (e.g. `https://continuum.ai`). No wildcards (`*`).
- [x] **Database:** Migrated from SQLite to managed PostgreSQL 15+ with SSL connection required (`sslmode=require`).
- [x] **TLS/HTTPS Termination:** Enforce TLS 1.3 with valid CA-signed certificates and HSTS headers enabled.
- [x] **Container:** Run container with non-root user (`appuser`, UID 10001).
- [x] **Volume Storage:** Read/write permissions strictly constrained to upload and ChromaDB directories.
- [x] **Automated Security Validation:** Built-in `validate_production_security()` passes during application startup.

---

## 2. Environment Variables & Secret Management

Never check production `.env` files into version control. Store secrets in your deployment provider's secret vault (e.g., AWS Secrets Manager, HashiCorp Vault, Render Environment Variables).

```bash
# Generate high-entropy secret keys:
openssl rand -hex 32
```

### Production `.env` Template
```ini
# Production Environment Flag
ENVIRONMENT=production

# Managed PostgreSQL Database
DATABASE_URL=postgresql+psycopg2://continuum_prod_user:SuperStrongDbPassword123!@db-host.internal:5432/continuum_ai?sslmode=require

# Authentication & Sessions
JWT_SECRET_KEY=b4a92f8d3c1e7a5b60284e91f0c2a7e4b918d3c5f2a1e8b7c4d0e9a2f1b8c7d6
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15

# Brute-Force & Lockout Thresholds
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15

# Strict Origin Allowlist (NO WILDCARDS)
CORS_ORIGINS=https://app.continuum.ai,https://continuum.ai

# AI Engine
AI_PROVIDER=gemini
AI_API_KEY=AIzaSyD...your_production_gemini_key...
AI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Storage Limits
CHROMA_PERSIST_DIRECTORY=/app/data/chroma_data
UPLOAD_DIRECTORY=/app/data/uploads
MAX_UPLOAD_SIZE=20971520
```

---

## 3. Production Database Hardening (PostgreSQL)

While local development uses SQLite, production deployments must use a hardened PostgreSQL cluster:

### 3.1 Migration Steps
1. Create a dedicated application database and unprivileged user:
   ```sql
   CREATE DATABASE continuum_ai;
   CREATE USER continuum_app WITH PASSWORD 'GenerateStrongPasswordHere';
   GRANT ALL PRIVILEGES ON DATABASE continuum_ai TO continuum_app;
   ```
2. Run Alembic database migrations:
   ```bash
   alembic upgrade head
   ```
3. Enable Row-Level Security (RLS) or periodic database snapshots.

---

## 4. Container & Dockerfile Hardening

Ensure the production Docker image follows the principle of least privilege:

```dockerfile
# Production Dockerfile
FROM python:3.11-slim as base

# 1. Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Create non-root system group and user
RUN groupadd -g 10001 continuum && \
    useradd -u 10001 -g continuum -s /bin/bash -m continuum

WORKDIR /app

# 3. Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy backend application source
COPY backend/ /app/backend/
COPY alembic.ini /app/

# 5. Create storage directories with restricted ownership
RUN mkdir -p /app/data/uploads /app/data/chroma_data && \
    chown -R continuum:continuum /app/data

# 6. Switch to unprivileged user
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]
```

---

## 5. Reverse Proxy & TLS Configuration (Nginx)

Place a hardened reverse proxy in front of the FastAPI ASGI workers:

```nginx
# /etc/nginx/conf.d/continuum.conf

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;

server {
    listen 80;
    server_name app.continuum.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.continuum.ai;

    ssl_certificate /etc/letsencrypt/live/app.continuum.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.continuum.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # OWASP Recommended Security Headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https:;" always;

    # Maximum client request body (matches MAX_UPLOAD_SIZE)
    client_max_body_size 25M;

    # Authentication route rate limiting
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=40 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend Single Page Application
    location / {
        root /var/www/continuum_frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 6. Backup & Disaster Recovery

Continuum AI stores state in three locations:
1. **Relational Database** (PostgreSQL/SQLite) — users, metadata, tasks, passports, decisions, audit logs.
2. **Vector Database** (`chroma_data/`) — vector embeddings and semantic indexes.
3. **Document Storage** (`uploads/`) — original source files (PDF, DOCX, CSV).

### Automated Daily Backup Script
```bash
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/continuum_${BACKUP_DATE}"

mkdir -p "${BACKUP_DIR}"

# 1. Dump relational database
pg_dump -U continuum_app -h localhost -d continuum_ai | gzip > "${BACKUP_DIR}/db_dump.sql.gz"

# 2. Archive ChromaDB vector data
tar -czf "${BACKUP_DIR}/chroma_backup.tar.gz" -C /app/data chroma_data

# 3. Archive uploaded document store
tar -czf "${BACKUP_DIR}/uploads_backup.tar.gz" -C /app/data uploads

# 4. Encrypt archive with GPG
tar -cf - "${BACKUP_DIR}" | gpg --encrypt --recipient ops@continuum.ai > "/backups/continuum_${BACKUP_DATE}.tar.gpg"
rm -rf "${BACKUP_DIR}"

echo "Continuum AI backup completed: /backups/continuum_${BACKUP_DATE}.tar.gpg"
```

---

## 7. Incident Response & Tamper Detection
- Query the global audit trail using `GET /api/projects/audit-logs/all` as an administrator.
- Filter on `ACCESS_DENIED_IDOR`, `ACCESS_DENIED_ROLE`, or `USER_LOGOUT` events to detect suspicious lateral movement attempts.
- In the event of compromised credentials, execute `POST /api/auth/logout-all` to instantly revoke all active refresh tokens for the affected user.

