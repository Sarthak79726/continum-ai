# Continuum AI — Technical Debt & Architectural Scalability Roadmap

**Date:** November 9, 2026  
**Document Target:** Engineering Leadership & DevOps Architects  
**Scope:** Architecture evolution from Local MVP / University Demonstration to Multi-Tenant Enterprise Production

---

## 1. Database Architecture & Concurrency

### Current State: SQLite with Foreign Key PRAGMA
- **Implementation:** Continuum AI currently uses a single SQLite database file (`continuum_ai.db`) accessed via SQLAlchemy 2.0 with connection pooling disabled and `PRAGMA foreign_keys=ON` enabled per connection.
- **Limitation:** SQLite uses database-level locking during write operations (`BEGIN IMMEDIATE` / `EXCLUSIVE`). While SQLite easily handles hundreds of concurrent read requests in WAL (Write-Ahead Logging) mode, concurrent write-heavy operations (e.g. 10 users uploading and processing multi-megabyte PDFs simultaneously) can trigger `sqlite3.OperationalError: database is locked`.

### Production Remediation: PostgreSQL Migration
1. **Zero Code Changes Needed:** The backend already uses pure SQLAlchemy declarative models (`Base.metadata`) and Pydantic schemas. 
2. **Migration Steps:**
   - Update `DATABASE_URL` in `.env` to `postgresql+psycopg2://user:password@postgres-host:5432/continuum_ai`.
   - Run `alembic upgrade head` to construct all tables, constraints, foreign keys, and indexes on PostgreSQL.
   - Configure a SQLAlchemy connection pool with `pool_size=20`, `max_overflow=10`, and `pool_pre_ping=True`.

---

## 2. Vector Database & Semantic Search Scalability

### Current State: Embedded ChromaDB
- **Implementation:** ChromaDB runs in embedded persistent client mode (`chromadb.PersistentClient(path="./chroma_data")`), saving vector indices directly on the local filesystem.
- **Limitation:** Embedded ChromaDB is bound to the single host process and cannot be shared across multiple horizontal container replicas without filesystem volume locking risks. Furthermore, storing millions of high-dimensional embeddings in local HNSW files degrades search latency and consumes substantial memory.

### Production Remediation: Dedicated Vector Infrastructure
1. **Tier 1 (PostgreSQL + pgvector):**
   - Consolidate relational and vector storage into PostgreSQL using the `pgvector` extension.
   - Vector chunk embeddings stored as `vector(384)` with HNSW or IVFFlat indexes, allowing transactional updates between document chunks and their embeddings.
2. **Tier 2 (Managed Vector Service - Qdrant / Pinecone):**
   - For multi-tenant SaaS deployments handling >100,000 documents, migrate the retrieval layer in `backend/app/services/vector_store/` to a dedicated Qdrant cluster with gRPC streaming and payload filtering by `tenant_id` and `project_id`.

---

## 3. Asynchronous Pipeline & Background Workers

### Current State: Synchronous FastAPI Ingestion
- **Implementation:** When a user uploads a document or triggers project analysis, chunking, embedding calculation, and AI extraction are executed in the request thread or standard FastAPI threadpool.
- **Limitation:** Processing a 100-page architectural specification can take 15–30 seconds. In HTTP request-response lifecycles, this risks client timeouts (HTTP 504) and blocks worker capacity.

### Production Remediation: Distributed Task Queue
- Implement a task queue using **Celery** or **ARQ** with **Redis** as the message broker.
- **Flow:**
  1. `POST /api/documents/upload` saves the raw file, creates a `Document` record with status `pending`, and enqueues a `process_document_task(doc_id)`.
  2. Background worker processes document chunks, computes embeddings, and updates the database.
  3. Frontend subscribes to progress updates via Server-Sent Events (SSE) or WebSockets (`/ws/projects/{id}/status`).

---

## 4. Machine Learning & Embedding Optimization

### Current State: In-Process PyTorch Model
- **Implementation:** `all-MiniLM-L6-v2` runs locally via `sentence-transformers` inside the FastAPI Python runtime on CPU.
- **Limitation:** PyTorch requires ~400MB RAM per worker process. Under multi-worker Uvicorn setups (`uvicorn --workers 4`), memory consumption scales linearly (1.6GB+), which exceeds cheap micro-container limits on AWS ECS / GCP Cloud Run.

### Production Remediation: Model Optimization & Microservices
1. **ONNX Runtime / TensorRT:** Convert `all-MiniLM-L6-v2` to ONNX format with 8-bit quantization (`int8`). This reduces inference latency by 3x and cuts RAM footprint to ~90MB.
2. **Dedicated Inference Service:** Deploy embedding generation as an internal microservice using Triton Inference Server or HuggingFace TEI (Text Embeddings Inference).

---

## 5. Security & Authentication Hardening

### Current State: Single Access Token
- **Implementation:** JWT authentication issues a signed token valid for 7 days (`ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7`).
- **Limitation:** If a token is compromised, it cannot be revoked before expiration without maintaining a server-side denylist.

### Production Remediation:
1. **Dual-Token System:** Transition to short-lived access tokens (15 minutes) and HTTP-only cookie refresh tokens (7 days).
2. **Token Revocation / Rotation:** Store active session IDs in Redis; rotate refresh tokens on each refresh call and revoke family sessions on anomalies.
3. **Rate Limiting:** Add `slowapi` rate limiting on `/api/auth/login` and `/api/ai/analyze` to prevent brute-force and resource exhaustion attacks.

---

## 6. Containerization & Production Deployment

### Current State: Dockerfile with Multi-Stage Build
The existing `Dockerfile` combines the Vite build with Uvicorn. For high-availability enterprise environments:
- **Frontend:** Serve built static assets via a CDN (Cloudflare / AWS CloudFront) backed by Nginx or S3 bucket storage.
- **Backend:** Run FastAPI container behind Traefik or an AWS Application Load Balancer with health checks (`/health`), non-root container users, and horizontal pod autoscaling (HPA) in Kubernetes.
