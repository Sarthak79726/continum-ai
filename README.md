# Continuum AI
### Intelligent Knowledge Handover & Project Continuity Platform

> *"Every project should remember what its people know."*

---

## 1. Project Overview & Problem Statement

### The Problem
When key engineers, team leads, or domain specialists leave a project or organization, critical context disappears. Project knowledge is typically fragmented across unstructured meeting notes, architecture diagrams, chat logs, pull requests, backlog tickets, and individual minds. New incoming engineers often spend weeks or months attempting to reconstruct:
- What has actually been built versus what was merely planned.
- Why critical architecture decisions were made.
- Where hidden dependencies and missing credentials reside.
- What active blockers and vulnerabilities threaten upcoming deadlines.

### The Solution: Continuum AI
Continuum AI is an enterprise-grade AI knowledge extraction, verification, and continuation platform. It continuously connects authorized project documentation, reconstructs actual technical state, links every claim to source text citations in an **Evidence Passport**, allows human governance in a **Review Centre**, and synthesizes an actionable **Continuity Blueprint** and downloadable PDF handover dossier.

Continuum AI implements the **5 Epistemic Stages**:
1. **CONNECT** — Collect and process authorized project information (.pdf, .docx, .csv, .txt).
2. **RECONSTRUCT** — Analyze documents to extract real tasks, architecture decisions, risks, and dependencies.
3. **VERIFY** — Ground every extracted assertion in direct source snippets with verification status and quality indicators.
4. **REVIEW** — Empower team leads and reviewers to audit, edit, approve, or reject dossiers with immutable review logs.
5. **HANDOVER** — Deliver a continuation-focused blueprint and professional ReportLab PDF dossier to the successor engineer.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19 + TypeScript + Vite | Enterprise SaaS UI, responsive layout, type safety |
| **Styling** | Tailwind CSS v4 | Professional typography, clean cards, subtle shadows |
| **Icons & Charts** | Lucide React + Recharts | High-density telemetry, pie charts, and risk severity bar charts |
| **Routing & HTTP** | React Router v7 + Axios | Client navigation, JWT authorization interceptor |
| **Backend API** | Python 3.11+ / FastAPI | High-concurrency REST API, dependency injection, async pipelines |
| **Database** | SQLite + SQLAlchemy 2.0 | Clean local persistence with direct PostgreSQL parity |
| **Vector Database** | ChromaDB Persistent Store | Project-isolated semantic vector collections |
| **Embeddings** | Modular 384-dim Dense Hashing / Transformers | Standalone, zero-network-dependency semantic vector embeddings |
| **Document Processing** | PyMuPDF, python-docx, pandas | Multi-format text extraction, cleaning, and sliding chunker |
| **Report Generation** | ReportLab | High-fidelity downloadable PDF handover dossiers |
| **Authentication** | PyJWT + Bcrypt | Role-Based Access Control (Admin, PM, Member, Incoming) |

---

## 3. Architecture & System Flow

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

## 4. Key Application Pages & Features

1. **Authentication (`/login`)**:
   - Secure login and registration with bcrypt password hashing and JWT tokens.
   - Pre-configured 1-click demo login (`demo@continuum.ai` / `password123`).
2. **Main Dashboard (`/`)**:
   - 6 Key Metrics: Total Projects, Indexed Documents, Completed Milestones, Pending Tasks, Risks, Handover Dossiers.
   - Interactive Recharts donut chart for task distribution and bar chart for risk severity.
   - Audit trail activity timeline and recent document tracking.
3. **Project Management (`/projects`)**:
   - Project CRUD, search, and status filtering (`active`, `completed`, `archived`).
   - Project cards displaying document, task, and risk telemetry.
4. **Project Details Studio (`/projects/:id`)**:
   - 8 Tabs: Overview, Documents, Tasks, Decisions, Dependencies, Risks, Knowledge Graph, Handovers.
   - Prominent **ANALYSE PROJECT** button triggering the AI knowledge reconstruction pipeline.
5. **Document Ingestion (`/documents`)**:
   - Drag-and-drop multi-file upload for PDF, DOCX, TXT, and CSV.
   - Real-time status: `uploaded`, `processing`, `processed`, `failed`.
   - Chunk inspection modal displaying extracted text chunks and page numbers.
6. **Knowledge Graph (`/graph`)**:
   - Interactive SVG relationship canvas visualizing People (Rahul, Sarah), Projects, Technical Components, Tasks, Decisions, Risks, and Dependencies.
   - Zoom, Pan, Reset controls, Category filtering, and detailed node inspector drawer.
7. **Evidence Passport (`/evidence`)**:
   - EPISTEMIC GROUNDING: Every AI-extracted claim displays its supporting document, page number, and exact text snippet.
   - Understandable quality labels: *Direct Citation*, *Inferred*, *Conflicting*, *Insufficient Context* (no arbitrary uncalibrated percentages).
   - Human audit modal allowing authorized reviewers to update verification status.
8. **Continuity Blueprint (`/tasks`)**:
   - Prioritized continuation plan for the incoming developer.
   - Clear distinction between extracted historical facts and AI recommendations.
   - Inline task status and priority controls.
9. **Handover Report Generator (`/handovers`)**:
   - Comprehensive 14-section dossier generator.
   - Toggle between **Incoming Member View** (practical continuation focus) and **Project Manager View** (governance focus).
   - One-click export to a styled, professional ReportLab PDF.
10. **Review Centre (`/reviews`)**:
    - Queue of pending, approved, and rejected handover reports.
    - Explicit sign-off workflows: reports cannot be marked approved without reviewer action.
11. **Team & Access Governance (`/team`)**:
    - Backend-enforced Role-Based Access Control (`ADMIN`, `PROJECT_MANAGER`, `TEAM_MEMBER`, `INCOMING_MEMBER`).
    - Project membership assignment and role management.
12. **Settings & Telemetry (`/settings`)**:
    - Live AI provider status, model name, ChromaDB storage path, and database info.

---

## 5. Demonstration Dataset: Smart Campus Management System

Continuum AI includes an out-of-the-box synthetic demonstration dataset representing a realistic knowledge handover:
- **Project Name:** `Smart Campus Management System (DEMO)`
- **Departing Developer:** `Rahul` (Lead Backend Engineer)
- **4 Synthetic Source Documents Generated on Disk:**
  1. `project_overview.pdf`: Details completed student authentication, JWT tokens, and campus department models.
  2. `meeting_notes.txt`: Captures sprint discussions, the blocked payment integration, and database architecture decisions.
  3. `task_status.csv`: Tabular record of TSK-101 through TSK-106 with status and ownership.
  4. `technical_updates.docx`: Details system dependencies, missing payment sandbox credentials, and technical risks.
- **One-Click Loading:** Click **"Load Demo"** in the sidebar or dashboard to automatically index and analyze this dataset.
- **Safety:** The demonstration data is strictly labeled as `DEMO DATA` and can be purged at any time via the trash icon.

---

## 6. Installation & Quickstart

### Prerequisites
- **Python:** 3.11+
- **Node.js:** v18+ (tested on v24.18.0)
- **Git**

### Step 1: Clone & Environment Setup
```bash
git clone <repository-url> continuum-ai
cd continuum-ai

# Copy environment template
cp .env.example .env
```

### Step 2: Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run backend tests to verify environment
pytest backend/tests/test_backend.py
```

### Step 3: Frontend Setup
```bash
# Navigate to frontend and install packages
cd frontend
npm install

# Test build
npm run build
cd ..
```

---

## 7. Running the Application

### Option A: Running Backend & Frontend in Separate Terminals

**Terminal 1 (Backend API):**
```bash
uvicorn app.main:app --app-dir ./backend --reload --port 8000
```
Backend API will be live at: `http://127.0.0.1:8000`  
Swagger API Documentation: `http://127.0.0.1:8000/docs`

**Terminal 2 (Frontend Client):**
```bash
cd frontend
npm run dev
```
Frontend Web Application will be live at: `http://localhost:5173`

---

## 8. Demo Credentials & First Walkthrough

### Credentials
- **Email:** `demo@continuum.ai`
- **Password:** `password123`
- *Or use the "1-Click Demo Login" button on the login screen.*

### 10-Minute Hackathon Demonstration Script
1. **Login:** Open `http://localhost:5173/login` and click **"1-Click Demo Login"**.
2. **Dashboard:** Notice the live Mission Control overview with project metrics and Recharts visualizations.
3. **Load Demo Data:** Click **"Load Demo"** in the bottom-left sidebar. This creates the *Smart Campus Management System*, ingests all 4 source files, creates dense vectors, and runs AI reconstruction.
4. **Inspect Documents:** Navigate to `Documents` to view the 4 ingested files (`.pdf`, `.txt`, `.csv`, `.docx`). Click the eye icon on `meeting_notes.txt` to inspect the extracted text chunks.
5. **Inspect Claims in Evidence Passport:** Navigate to `Evidence Passport`. Observe how each claim (e.g. *"Payment integration is incomplete"*) is grounded in the exact source quote (*"Payment gateway sandbox credentials are still awaited"*). Click **Audit** to change verification status.
6. **Explore Knowledge Graph:** Navigate to `Knowledge Graph`. Observe the interactive topology showing Rahul connected to Authentication, the Payment API dependency on Gateway Credentials, and critical blockers in red.
7. **Continuity Blueprint:** Navigate to `Continuity Blueprint`. Review the prioritized next-step action sequence for Rahul's successor.
8. **Generate Handover Dossier:** Navigate to `Handover Reports`. View the 14-section report, toggle between *Incoming Member View* and *PM Audit View*, and click **Export PDF** to download the professional ReportLab document.
9. **Review Centre Sign-off:** Navigate to `Review Centre`. Approve the dossier with governance sign-off remarks.

---

## 9. Environment Configuration Options

In `.env`:
```ini
# Database (Default: SQLite local database with zero setup)
DATABASE_URL=sqlite:///./continuum_ai.db

# JWT Security
JWT_SECRET_KEY=continuum-ai-super-secret-key-change-in-production-2025
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Provider Configuration
# Supported: demo, gemini, openai, groq, ollama
AI_PROVIDER=demo
AI_API_KEY=
AI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Storage Directories
CHROMA_PERSIST_DIRECTORY=./chroma_data
UPLOAD_DIRECTORY=./uploads
```

*Note: Paid API keys are never required to run or test Continuum AI. In `demo` mode, the deterministic local NLP extraction engine parses real uploaded document text without external network dependencies.*

---

## 10. Folder Structure

```
continuum-ai/
├── .env.example                    # Environment variable template
├── .env                            # Local configuration file
├── requirements.txt                # Python backend dependencies
├── package.json                    # Workspace scripts
├── README.md                       # Comprehensive system documentation
├── continuum_ai.db                 # SQLite relational database
├── chroma_data/                    # ChromaDB vector index storage
├── uploads/                        # Ingested project documents by project ID
├── data/
│   └── sample_documents/           # Synthetic sample dataset (.pdf, .txt, .csv, .docx)
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application, CORS, routers, and seeding
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings configuration
│   │   │   ├── security.py         # Bcrypt password hashing & JWT tokens
│   │   │   └── dependencies.py     # Auth session & RBAC project access guards
│   │   ├── database/
│   │   │   └── session.py          # SQLAlchemy engine and SessionLocal
│   │   ├── models/
│   │   │   └── all_models.py       # User, Project, Document, Chunk, Evidence, Task, Risk, etc.
│   │   ├── schemas/
│   │   │   └── all_schemas.py      # Strict Pydantic input/output schemas
│   │   ├── services/
│   │   │   ├── document_processor/ # PyMuPDF, python-docx, pandas, txt parsers & chunker
│   │   │   ├── embeddings/         # 384-dim standalone dense semantic embedding service
│   │   │   ├── vector_store/       # ChromaDB persistent collection manager
│   │   │   ├── retrieval/          # ProjectRetriever ranking and context formatting
│   │   │   ├── ai_engine/          # Gemini, OpenAI, and Local NLP providers & prompts
│   │   │   ├── knowledge_extractor/# End-to-end 8-category knowledge reconstruction
│   │   │   ├── evidence_verifier/  # Evidence passport linking & cross-source conflict detection
│   │   │   ├── handover_generator/ # 14-section builder & ReportLab PDF exporter
│   │   │   └── sample_data/        # Synthetic Smart Campus demo generator
│   │   └── api/                    # 13 REST API route modules
│   └── tests/
│       └── test_backend.py         # Pytest test suite
│
└── frontend/
    ├── index.html                  # HTML entrypoint with Continuum branding
    ├── vite.config.ts              # Vite configuration with Tailwind CSS & proxy
    ├── tsconfig.json               # TypeScript configuration
    └── src/
        ├── App.tsx                 # Client routing and protected routes
        ├── index.css               # Tailwind CSS v4 styling rules
        ├── types/                  # TypeScript interfaces
        ├── services/api.ts         # Axios client and typed API functions
        ├── context/AuthContext.tsx # React Authentication context
        ├── components/
        │   ├── common/             # Badge, Modal, EmptyState
        │   └── layout/             # Navbar, Sidebar, Shell Layout
        └── pages/                  # 12 Enterprise Pages (Login, Dashboard, Projects, Detail, etc.)
```

---

## 11. Known Limitations & Future Scope

### Known Limitations
- Vector index uses local ChromaDB and dense semantic hashing; for multi-terabyte enterprise data, deployment to distributed Chroma or Milvus is advised.
- Document extraction currently supports PDF, DOCX, TXT, and CSV; scanned OCR images require Tesseract or cloud Vision OCR.

### Future Scope
- Automated Git repository commit and PR ingestion to directly link code commits to extracted tasks.
- Slack and Microsoft Teams integration to capture implicit decisions made in technical communication channels.
- Real-time collaborative review comments on individual sections of the handover dossier.

---

## 12. License
MIT License. Built for university hackathons, research evaluations, and enterprise SaaS continuity management.

