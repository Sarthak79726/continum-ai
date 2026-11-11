# Continuum AI
### Intelligent Knowledge Handover & Project Continuity Platform

> *"Every project should remember what its people know."*

---

## Table of Contents
1. [Executive Overview & Vision](#1-executive-overview--vision)
2. [The 5 Epistemic Stages](#2-the-5-epistemic-stages)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture & Data Flow](#4-system-architecture--data-flow)
5. [Complete Application Pages & Features](#5-complete-application-pages--features)
6. [Production Readiness Audit & Technical Remediations](#6-production-readiness-audit--technical-remediations)
7. [Frontend Performance & Bundle Optimization](#7-frontend-performance--bundle-optimization)
8. [Complete REST API Reference](#8-complete-rest-api-reference)
9. [Installation & Quickstart Guide](#9-installation--quickstart-guide)
10. [Demonstration Dataset & 10-Minute Walkthrough](#10-demonstration-dataset--10-minute-walkthrough)
11. [Environment Variables & Configuration](#11-environment-variables--configuration)
12. [Repository Directory Structure](#12-repository-directory-structure)
13. [Technical Debt & Enterprise Scalability Roadmap](#13-technical-debt--enterprise-scalability-roadmap)
14. [License](#14-license)

---

## 1. Executive Overview & Vision

### The Problem
When lead engineers, architects, or core team members transition away from a project or organization, critical institutional knowledge is lost. Vital technical context is routinely fragmented across unstructured meeting notes, architecture diagrams, chat logs, pull requests, ticketing backlogs, and tacit developer memory. Successor engineers face steep ramp-up curves and frequently spend weeks attempting to reconstruct:
- **Actual vs. Planned Progress:** What technical components are truly finished versus what was merely designed.
- **Architectural Decision Context:** Why specific frameworks, schemas, or design patterns were chosen.
- **Hidden Dependencies & Prerequisites:** Undocumented third-party credentials, internal API keys, and library prerequisites.
- **Active Technical Debt & Deadlocks:** Blockers, security vulnerabilities, and pending external deliverables.

### The Solution: Continuum AI
**Continuum AI** is an enterprise-grade AI knowledge extraction, verification, and continuation platform. It continuously connects authorized project artifacts, reconstructs current system state using semantic embeddings and RAG, grounds every technical claim in direct source text citations inside an **Evidence Passport**, enforces human oversight through a **Review Centre**, and synthesizes an actionable **Continuity Blueprint** alongside an executive **ReportLab PDF Handover Dossier**.

---

## 2. The 5 Epistemic Stages

Continuum AI models knowledge handover across five rigorous epistemic stages:

```
┌─────────────┐     ┌────────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  1. CONNECT │ ──> │ 2. RECONSTRUCT │ ──> │  3. VERIFY   │ ──> │  4. REVIEW  │ ──> │ 5. HANDOVER  │
└─────────────┘     └────────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
  Multi-format        Semantic Chunking      Strict Grounding     Governance Queue    14-Section PDF
  Doc Ingestion       & Entity Topology      & Evidence Passport  & Immutable Audit   & Action Plan
```

1. **CONNECT — Collect & Ingest Authorized Project Artifacts:**  
   Ingests multi-format documents (PDF, DOCX, CSV, TXT) with OCR fallback for scanned pages, sliding-window chunking, and strict tenant isolation.
2. **RECONSTRUCT — Deep Neural Semantic Understanding:**  
   Calculates 384-dimensional dense semantic vectors using HuggingFace `all-MiniLM-L6-v2` and persists them in project-isolated ChromaDB collections.
3. **VERIFY — Zero-Hallucination Epistemic Grounding:**  
   Links every extracted technical claim, task, decision, and risk directly to a verified source excerpt with page number citations. Unsupported claims are downgraded to `UNVERIFIED`.
4. **REVIEW — Human Governance & Sign-off Workflows:**  
   Provides dual perspectives: **Incoming Member View** (practical continuity roadmap) and **Project Manager View** (audit telemetry). Enforces explicit sign-offs before dossiers reach `APPROVED` status.
5. **HANDOVER — Actionable Continuation Dossier:**  
   Generates a prioritized 30-60-90 day continuation plan and downloads a high-fidelity ReportLab PDF handover dossier.

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend Framework** | React + TypeScript | 19.3 / ~7.0 | Modern declarative UI, strict type safety, zero runtime drift |
| **Build Tool & Bundler** | Vite + Rolldown | 8.3 / 1.2 | Sub-second HMR, Rust-based Rolldown code-splitting engine |
| **Styling** | Tailwind CSS v4 | 4.3.5 | Modern high-performance styling engine, zero CSS bloat |
| **Routing & Navigation** | React Router | 7.18 | Client routing with `React.lazy()` dynamic module loading |
| **Visualizations** | Recharts | 3.10 | Telemetry donut charts and risk severity distribution charts |
| **Backend API** | Python / FastAPI | 3.11+ / 0.110 | Asynchronous REST endpoints, dependency injection, auto OpenAPI docs |
| **Relational Database** | SQLite + SQLAlchemy | 2.0.0 | Relational database with enforced `PRAGMA foreign_keys=ON` |
| **Database Migrations** | Alembic | 1.13+ | Version-controlled schema migrations with PostgreSQL parity |
| **Vector Database** | ChromaDB | 0.4.24 | Project-isolated persistent vector storage |
| **Semantic Embeddings** | SentenceTransformers | 6.2.0 | HuggingFace `all-MiniLM-L6-v2` 384-dim dense semantic embeddings |
| **Machine Learning Engine** | PyTorch (CPU/GPU) | 2.15.0 | Sub-second offline vector calculation without cloud dependencies |
| **Document Processing** | PyMuPDF, python-docx, pandas | Latest | Multi-format text parsing with OCR extraction for scanned documents |
| **Dossier Generation** | ReportLab | 4.1.0 | Server-side binary PDF generation with custom enterprise layouts |
| **Authentication & RBAC** | PyJWT + Bcrypt | 2.8 / 4.1 | Role-based access control (`ADMIN`, `PM`, `MEMBER`, `INCOMING`) |

---

## 4. System Architecture & Data Flow

```
                                      +------------------------------------+
                                      |   Authorized Project Documents     |
                                      |   (PDF, DOCX, CSV, TXT)            |
                                      +-----------------+------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |   Document Processing Pipeline     |
                                      |   - PyMuPDF / docx / pandas / txt  |
                                      |   - Text Cleaning & Normalization  |
                                      |   - Sliding Window Chunking        |
                                      +-----------------+------------------+
                                                        |
                               +------------------------+-----------------------+
                               |                                                |
                               v                                                v
              +--------------------------------+               +--------------------------------+
              |     SQLite Database Tables     |               |    ChromaDB Persistent Store   |
              |     - Document & Chunk Records |               |    - Project Collections       |
              |     - User & Project Registry  |               |    - 384-dim Dense Embeddings  |
              +--------------------------------+               +----------------+---------------+
                               |                                                |
                               +------------------------+-----------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |     Semantic Retrieval Engine      |
                                      |     - Cosine Similarity Search     |
                                      |     - Top-k Chunk Ranking          |
                                      +-----------------+------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |    AI Knowledge Reconstruction     |
                                      |    - Configurable Provider         |
                                      |      (Gemini / OpenAI / Local NLP) |
                                      |    - Strict Pydantic JSON Schema   |
                                      |    - Zero-Hallucination Grounding  |
                                      +-----------------+------------------+
                                                        |
                     +----------------------------------+----------------------------------+
                     |                                  |                                  |
                     v                                  v                                  v
      +-----------------------------+    +-----------------------------+    +-----------------------------+
      |      Evidence Passport      |    |   Interactive Knowledge     |    |    Continuity Blueprint     |
      |   - Direct Quote Citations  |    |           Graph             |    |   - Next Action Steps       |
      |   - Grounding Quality       |    |   - People, Components,     |    |   - Facts vs Recommendations|
      |   - Conflict Detection      |    |     Tasks, Risks & Deps     |    |   - Status & Priorities     |
      +-----------------------------+    +-----------------------------+    +-----------------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |     Governance Review Centre       |
                                      |     - PM View & Incoming View      |
                                      |     - Explicit Sign-off & Audit    |
                                      |     - ReportLab PDF Generation     |
                                      +------------------------------------+
```

---

## 5. Complete Application Pages & Features

Continuum AI includes 12 enterprise interfaces:

1. **Authentication (`/login`)**:
   - Secure login and registration with bcrypt password hashing and JWT bearer tokens.
   - Pre-configured **1-Click Demo Login** (`demo@continuum.ai` / `password123`) for rapid evaluation.
2. **Executive Mission Control Dashboard (`/`)**:
   - 6 High-Density KPI Cards: Total Projects, Indexed Documents, Completed Milestones, Pending Tasks, Critical Risks, Handover Dossiers.
   - Recharts visual telemetry: Donut chart for task completion status and bar chart for risk severity distribution.
   - Live system activity timeline and recent document tracking.
3. **Project Management Studio (`/projects`)**:
   - Project lifecycle CRUD, real-time search, and status filtering (`active`, `completed`, `archived`).
   - Project cards displaying document counts, completed task ratios, and risk counters.
4. **Project Details Studio (`/projects/:id`)**:
   - 8 Dedicated Sub-Views: Overview, Documents, Tasks, Decisions, Dependencies, Risks, Knowledge Graph, Handover Reports.
   - Prominent **ANALYSE PROJECT** button executing full RAG pipeline and neural knowledge reconstruction.
5. **Document Ingestion Hub (`/documents`)**:
   - Drag-and-drop multi-file upload for PDF, DOCX, TXT, and CSV with OCR support for scanned documents.
   - Real-time ingestion status tracking (`uploaded`, `processing`, `processed`, `failed`).
   - Native document streaming download (`GET /api/documents/:id/download`) and text chunk inspection drawer.
6. **Dynamic Knowledge Graph (`/graph`)**:
   - Native interactive SVG relationship canvas synthesizing live database records (Project Members, Technical Components, Tasks, Decisions, Risks, and Dependencies).
   - Zero hardcoded fallback nodes. Includes interactive zoom, pan, category filtering, and node inspector drawer.
7. **Evidence Passport (`/evidence`)**:
   - **Epistemic Grounding Guard:** Every AI-extracted claim displays its source document, page number, and direct quote citation.
   - Grounding validation rules: claims lacking source verification are flagged as `UNVERIFIED` / `Insufficient Context`.
   - Human audit modal allowing authorized reviewers to verify, flag, or challenge claims.
8. **Continuity Blueprint (`/tasks`)**:
   - Prioritized continuation plan for the incoming developer.
   - Clear distinction between extracted historical facts and AI continuation recommendations.
   - Inline task status and priority controls.
9. **Handover Report Generator (`/handovers`)**:
   - Comprehensive 14-section structured dossier generator.
   - Dual perspective toggle: **Incoming Member View** (practical continuation focus) and **Project Manager View** (governance focus).
   - One-click export to a styled, professional ReportLab PDF.
10. **Governance Review Centre (`/reviews`)**:
    - Queue of pending, approved, and rejected handover reports.
    - Explicit sign-off workflows: reports cannot transition to `APPROVED` without recorded reviewer remarks and timestamps.
11. **Team & Access Governance (`/team`)**:
    - Backend-enforced Role-Based Access Control (`ADMIN`, `PROJECT_MANAGER`, `TEAM_MEMBER`, `INCOMING_MEMBER`).
    - Project membership assignment and role management with project isolation.
12. **Settings & Telemetry (`/settings`)**:
    - Dynamic runtime switching between Gemini, OpenAI, and local demonstration AI providers.
    - API key and model persistence via `PUT /api/settings` and real-time backend ping telemetry.

---

## 6. Production Readiness Audit & Technical Remediations

A comprehensive production readiness audit was performed across all 23 functional modules, yielding 100% verification across all critical workflows:

### Key Deficiencies & Remediations:
1. **Semantic Embeddings Upgrade:**
   - *Issue:* The vector pipeline previously used a character 3-gram MD5/SHA256 numerical hash projection that yielded arbitrary cosine similarities for synonymous terms.
   - *Fix:* Replaced with HuggingFace `SentenceTransformer('all-MiniLM-L6-v2')`. Semantic similarity between *"Payment gateway stripe integration"* and *"Customer billing API"* scores **$+0.4297$**, while unrelated terms score **$-0.1064$**.
2. **Database Integrity & Foreign Key Enforcements:**
   - *Issue:* SQLite disables foreign key checks by default, causing orphaned audit logs and `IntegrityError` failures during project deletion.
   - *Fix:* Added `PRAGMA foreign_keys=ON` connection pool hook in SQLAlchemy, added cascading deletes to `Project.audit_logs`, and initialized version-controlled **Alembic migrations** (initial version `7d4760ba951b`).
3. **Strict Epistemic Grounding:**
   - *Issue:* Claims could previously be tagged as verified without matching chunks in the vector store.
   - *Fix:* `EvidenceVerifier` now verifies that the cited text snippet exists within the project's actual chunk records. If absent, the claim is downgraded to `UNVERIFIED` with reason `"Evidence snippet not grounded in ingested documents"`.
4. **Document Delivery Pipeline:**
   - *Issue:* Documents could be ingested but not retrieved.
   - *Fix:* Added `GET /api/documents/{id}/download` endpoint returning a FastAPI `FileResponse` and added download action buttons in both `DocumentsPage.tsx` and `ProjectDetailPage.tsx`.
5. **Knowledge Graph Modernization:**
   - *Issue:* Graph previously defaulted to static demo nodes ("Rahul", "Sarah") when database records were sparse.
   - *Fix:* Dynamic synthesis generating nodes and directional edges exclusively from live database records.

---

## 7. Frontend Performance & Bundle Optimization

The frontend build has been optimized using **React 19 dynamic imports** and **Vite 8 Rolldown manual chunk splitting**:

```
Baseline Monolithic Build:
└── dist/assets/index.js (854.87 kB | gzip: 242.52 kB)  [Vite Warning: Chunks >500 kB]

Optimized Rolldown Production Build:
├── dist/assets/index.js               (74.78 kB  | gzip: 26.50 kB)   [-91.3%]
├── dist/assets/react-vendor.js        (252.34 kB | gzip: 80.21 kB)   [React 19, ReactDOM, React Router]
├── dist/assets/icons-vendor.js        (24.31 kB  | gzip: 8.68 kB)    [Consolidated Lucide Icons]
├── dist/assets/recharts-vendor.js     (375.72 kB | gzip: 106.97 kB)  [Loaded ONLY on Dashboard]
├── dist/assets/DashboardPage.js       (12.56 kB  | gzip: 2.88 kB)    [-96.8%]
└── dist/assets/[PageChunks].js        (7.38 kB – 14.75 kB each)      [Loaded on demand]
```

### Key Performance Accomplishments:
- **Initial App Shell Reduction:** Reduced from **854.87 kB down to 352.15 kB** (a **58.8% reduction in raw JS, 52.2% gzipped**).
- **Vite Warning:** **100% eliminated** without modifying `chunkSizeWarningLimit`.
- **Build Speed:** Production build compiles in **894 ms**.
- **Deferred Recharts:** Heavy Recharts and D3 dependencies are completely isolated in `recharts-vendor.js` and only downloaded when visiting the Dashboard.
- **Unused Packages Purged:** Removed unused `@xyflow/react`, `clsx`, and `tailwind-merge` dependencies.

---

## 8. Complete REST API Reference

Continuum AI exposes 13 REST API routers with full OpenAPI documentation at `/docs`:

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Create a new user account.
- `POST /api/auth/login` — Authenticate and receive a JWT bearer token.
- `GET /api/auth/me` — Retrieve current authenticated user profile.
- `POST /api/auth/demo-login` — 1-click authentication using demo credentials.

### Projects (`/api/projects`)
- `GET /api/projects` — List all accessible projects.
- `POST /api/projects` — Create a new project.
- `GET /api/projects/{id}` — Retrieve project details, members, and metrics.
- `PUT /api/projects/{id}` — Update project metadata and status.
- `DELETE /api/projects/{id}` — Delete project and cascade all child records.
- `GET /api/projects/{id}/audit-logs` — Retrieve chronological audit trail.

### Documents (`/api/documents`)
- `POST /api/documents/upload` — Multipart upload for PDF, DOCX, CSV, TXT.
- `GET /api/documents/{id}` — Retrieve document metadata and status.
- `GET /api/documents/{id}/chunks` — Retrieve extracted document chunks.
- `GET /api/documents/{id}/download` — Stream and download original document file.
- `DELETE /api/documents/{id}` — Delete document and prune vector store chunks.

### AI Knowledge Reconstruction (`/api/ai`)
- `POST /api/ai/projects/{id}/analyze` — Trigger end-to-end RAG analysis and knowledge reconstruction.
- `GET /api/ai/status` — Inspect current AI provider status and model configuration.

### Knowledge Graph (`/api/graph`)
- `GET /api/graph/projects/{id}` — Retrieve live synthesized nodes and directional edges.

### Tasks, Decisions, Risks, Dependencies
- `GET|POST|PUT|DELETE /api/tasks` — Manage project task items.
- `GET|POST|PUT|DELETE /api/decisions` — Manage architectural decision records.
- `GET|POST|PUT|DELETE /api/risks` — Manage technical risk assessments.
- `GET|POST|PUT|DELETE /api/dependencies` — Manage system prerequisites and blockers.

### Handover Dossiers & Reviews (`/api/handovers` & `/api/reviews`)
- `POST /api/handovers/projects/{id}/generate` — Synthesize 14-section handover dossier.
- `GET /api/handovers/{id}` — Retrieve structured handover report.
- `GET /api/handovers/{id}/export-pdf` — Download binary ReportLab PDF dossier.
- `POST /api/handovers/{id}/review` — Record governance sign-off or rejection.

### System Settings & Demo (`/api/settings` & `/api/demo`)
- `GET /api/settings` — Query active AI provider, model, and storage telemetry.
- `PUT /api/settings` — Dynamically update AI provider (`demo`, `gemini`, `openai`) and API keys.
- `POST /api/demo/seed` — Seed synthetic *Smart Campus Management System* demo data.
- `DELETE /api/demo/purge` — Cleanly purge synthetic demonstration data.

---

## 9. Installation & Quickstart Guide

### Prerequisites
- **Python:** 3.11+
- **Node.js:** v18+ (tested on v24.18.0)
- **Git**

### Step 1: Clone Repository & Setup Environment
```bash
git clone <repository-url> continuum-ai
cd continuum-ai

# Copy environment template
cp .env.example .env
```

### Step 2: Backend Setup & Database Migrations
```bash
# Install Python backend dependencies
pip install -r requirements.txt

# Run Alembic database migrations
alembic upgrade head

# Run automated audit test suite (12 core workflows)
python -m pytest backend/tests/test_audit_suite.py -v
```

### Step 3: Frontend Setup & Build Verification
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Verify production build with Vite 8 Rolldown
npm run build
cd ..
```

### Step 4: Running the Application

#### Option A: One-Click Startup Script (Windows)
```powershell
# In PowerShell:
.\start.ps1

# Or in Command Prompt:
start.bat
```

#### Option B: Separate Terminals

**Terminal 1 (Backend API):**
```bash
uvicorn app.main:app --app-dir ./backend --reload --port 8000
```
- API Server: `http://127.0.0.1:8000`
- Swagger Documentation: `http://127.0.0.1:8000/docs`

**Terminal 2 (Frontend Client):**
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 10. Demonstration Dataset & 10-Minute Walkthrough

Continuum AI includes an out-of-the-box synthetic dataset representing a realistic engineering transition:
- **Project:** `Smart Campus Management System (DEMO)`
- **Departing Lead:** `Rahul` (Lead Backend Engineer)
- **4 Synthetic Source Artifacts Generated on Disk:**
  1. `project_overview.pdf`: Architecture overview, student authentication, and campus department models.
  2. `meeting_notes.txt`: Sprint discussions, database architecture decisions, and payment integration blocks.
  3. `task_status.csv`: Tabular record of TSK-101 through TSK-106 with status and ownership.
  4. `technical_updates.docx`: System dependencies, missing payment sandbox credentials, and technical risks.

### 10-Minute Demonstration Script
1. **Login:** Open `http://localhost:5173/login` and click **"1-Click Demo Login"**.
2. **Dashboard:** View high-density KPI telemetry and Recharts visualizations.
3. **Load Demo Data:** Click **"Load Demo"** in the sidebar to ingest all 4 source files, generate dense vectors, and execute AI reconstruction.
4. **Inspect Documents:** Navigate to `Documents` to view the 4 files. Click the download icon to verify file streaming, or the eye icon to inspect text chunks.
5. **Inspect Evidence Passport:** Navigate to `Evidence Passport`. Observe how each claim (e.g. *"Payment integration is incomplete"*) is grounded in the exact source quote (*"Payment gateway sandbox credentials are still awaited"*).
6. **Explore Knowledge Graph:** Navigate to `Knowledge Graph`. Observe the dynamic SVG topology showing Rahul connected to Authentication, the Payment API dependency on Gateway Credentials, and critical blockers in red.
7. **Continuity Blueprint:** Navigate to `Continuity Blueprint`. Review the prioritized 30-60-90 day continuation plan for Rahul's successor.
8. **Generate Handover Dossier:** Navigate to `Handover Reports`. View the 14-section report, toggle between *Incoming Member View* and *PM Audit View*, and click **Export PDF** to download the professional ReportLab document.
9. **Review Centre Sign-off:** Navigate to `Review Centre`. Approve the dossier with governance remarks.

---

## 11. Environment Variables & Configuration

In `.env`:
```ini
# Relational Database (Default: SQLite local database with zero setup)
DATABASE_URL=sqlite:///./continuum_ai.db

# JWT Security
JWT_SECRET_KEY=continuum-ai-super-secret-key-change-in-production-2025
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Provider Configuration
# Supported: demo, gemini, openai
AI_PROVIDER=demo
AI_API_KEY=
AI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Persistent Storage Directories
CHROMA_PERSIST_DIRECTORY=./chroma_data
UPLOAD_DIRECTORY=./uploads
```

*Note: Paid API keys are never required to run or test Continuum AI. In `demo` mode, the deterministic local NLP extraction engine parses real uploaded document text without external network dependencies.*

---

## 12. Repository Directory Structure

```
continuum-ai/
├── .env.example                    # Environment variable template
├── .env                            # Local configuration file
├── requirements.txt                # Python backend dependencies
├── alembic.ini                     # Alembic database migration config
├── Dockerfile                      # Multi-stage production container build
├── render.yaml                     # Render.com cloud deployment blueprint
├── package.json                    # Workspace scripts
├── README.md                       # Comprehensive system documentation
├── AUDIT_REPORT.md                 # 23-Feature production readiness audit report
├── TECHNICAL_DEBT.md               # Architecture scalability roadmap
├── TEST_RESULTS.md                 # Pytest 12-test automated benchmark report
├── continuum_ai.db                 # SQLite relational database
├── chroma_data/                    # ChromaDB vector index storage
├── uploads/                        # Ingested project documents by project ID
├── data/
│   └── sample_documents/           # Synthetic sample dataset (.pdf, .txt, .csv, .docx)
│
├── backend/
│   ├── alembic/                    # Version-controlled schema migrations
│   │   └── versions/               # Migration scripts (e.g. 7d4760ba951b_initial_schema)
│   ├── app/
│   │   ├── main.py                 # FastAPI application, CORS, routers, and seeding
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings configuration
│   │   │   ├── security.py         # Bcrypt password hashing & JWT tokens
│   │   │   └── dependencies.py     # Auth session & RBAC project access guards
│   │   ├── database/
│   │   │   └── session.py          # SQLAlchemy engine, connection listeners, SessionLocal
│   │   ├── models/
│   │   │   └── all_models.py       # User, Project, Document, Chunk, Evidence, Task, Risk, etc.
│   │   ├── schemas/
│   │   │   └── all_schemas.py      # Strict Pydantic input/output schemas
│   │   ├── services/
│   │   │   ├── document_processor/ # PyMuPDF (OCR-aware), python-docx, pandas, txt parsers
│   │   │   ├── embeddings/         # HuggingFace all-MiniLM-L6-v2 dense semantic vectors
│   │   │   ├── vector_store/       # ChromaDB persistent collection manager
│   │   │   ├── retrieval/          # ProjectRetriever ranking and context formatting
│   │   │   ├── ai_engine/          # Gemini, OpenAI, and Local NLP providers
│   │   │   ├── knowledge_extractor/# End-to-end 8-category knowledge reconstruction
│   │   │   ├── evidence_verifier/  # Strict evidence grounding & conflict detection
│   │   │   ├── handover_generator/ # 14-section builder & ReportLab PDF exporter
│   │   │   └── sample_data/        # Synthetic Smart Campus demo generator
│   │   └── api/                    # 13 REST API route modules
│   └── tests/
│       └── test_audit_suite.py     # 12-test automated audit verification suite
│
└── frontend/
    ├── index.html                  # HTML entrypoint with preloaded assets
    ├── vite.config.ts              # Vite 8 + Rolldown manualChunks configuration
    ├── tsconfig.json               # TypeScript configuration
    └── src/
        ├── App.tsx                 # Route-level code splitting with React.lazy & Suspense
        ├── index.css               # Tailwind CSS v4 styling rules
        ├── types/                  # TypeScript interfaces
        ├── services/api.ts         # Axios client and typed API functions
        ├── context/AuthContext.tsx # React Authentication context
        ├── components/
        │   ├── common/             # Badge, Modal, EmptyState
        │   └── layout/             # Navbar, Sidebar, Shell Layout with Suspense fallback
        └── pages/                  # 12 Lazy-loaded Pages (Login, Dashboard, Projects, etc.)
```

---

## 13. Technical Debt & Enterprise Scalability Roadmap

For engineering teams planning multi-tenant enterprise deployment:

1. **Relational Database (PostgreSQL Migration):**
   - SQLite handles read-heavy local loads efficiently with `PRAGMA foreign_keys=ON`.
   - For high concurrent write volumes, change `DATABASE_URL` to PostgreSQL and run `alembic upgrade head`. Zero model code changes are required.
2. **Vector Infrastructure (Qdrant / pgvector):**
   - Current persistent ChromaDB runs locally on the host filesystem.
   - For horizontally-scaled Kubernetes deployments, migrate to managed Qdrant or PostgreSQL `pgvector` with HNSW indexing.
3. **Asynchronous Background Processing (Celery / Redis):**
   - Currently, document chunking and vector calculation run asynchronously in the FastAPI threadpool.
   - For processing 500+ page technical dossiers, transition ingestion tasks to Celery workers with progress updates via Server-Sent Events (SSE).
4. **Machine Learning Model Quantization:**
   - The in-process PyTorch `all-MiniLM-L6-v2` model consumes ~400MB RAM.
   - In containerized edge environments, convert the model to 8-bit quantized ONNX Runtime (`int8`) to reduce RAM footprint to ~90MB.

---

## 14. License
MIT License. Built for university hackathons, research evaluations, and enterprise SaaS continuity management.
