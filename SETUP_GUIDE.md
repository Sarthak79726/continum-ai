# CONTINUUM AI — INSTALLATION, SETUP & RUN GUIDE
**Version:** 2.0 (Production Release)  
**Operating Systems Supported:** Windows 10/11, macOS, Linux  

---

## 1. System Prerequisites

Before starting, verify that your environment has:
- **Python:** 3.11, 3.12, 3.13, or 3.14
- **Node.js:** 18.x, 20.x, 22.x, or 24.x
- **Package Managers:** `pip` (Python) and `npm` (Node)
- **Git:** Version control CLI

---

## 2. Fast-Start Local Commands (Recommended)

To run the entire full-stack application concurrently:

### Terminal 1: Backend Server (FastAPI + Uvicorn)
```powershell
# Navigate to workspace root
cd "e:\continum ai"

# Install backend dependencies (if not already installed)
pip install -r backend/requirements.txt

# Run database migrations
cd backend
alembic upgrade head
cd ..

# Start FastAPI API server on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API is now accessible at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

### Terminal 2: Frontend Server (React 19 + Vite 8)
```powershell
# Navigate to frontend directory
cd "e:\continum ai\frontend"

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
The frontend is now accessible at:
- **Web Application:** `http://localhost:5173`

---

## 3. Pre-Seeded Demo Account Credentials

You do not need to register a new account to evaluate the platform. Use the built-in credentials or the 1-click button on the login screen:

- **Email:** `demo@continuum.ai`
- **Password:** `password123`
- **Role:** `ADMIN` / Technical Lead
- **1-Click Button:** Click **`1-Click Demo Login (demo@continuum.ai)`** at the bottom of the sign-in form.

---

## 4. Building the Frontend for Production

Continuum AI uses Vite 8 with the Rolldown compiler and lazy route-level code splitting:

```powershell
npm --prefix frontend run build
```

**Expected Build Output:**
- 2,523 modules transformed
- Zero bundle warnings (all chunks under 500 kB)
- Sub-2 second compilation

To preview the production build locally:
```powershell
npm --prefix frontend run preview
```

---

## 5. Running the Complete Automated Test Suite

Continuum AI features a comprehensive 16-test audit suite verifying database persistence, RBAC, document chunking, semantic embeddings, knowledge graphs, employee passports, and grounded RAG:

```powershell
python -m pytest backend/tests/test_audit_suite.py -v
```

**Expected Output:**
```
============================= test session starts =============================
collected 16 items

backend/tests/test_audit_suite.py::test_1_user_registration_and_login PASSED
backend/tests/test_audit_suite.py::test_2_project_crud_and_cascade_delete PASSED
backend/tests/test_audit_suite.py::test_3_document_parsers_pdf_docx_csv_txt PASSED
backend/tests/test_audit_suite.py::test_4_embedding_service_semantic_model PASSED
backend/tests/test_audit_suite.py::test_5_ai_knowledge_reconstruction_pipeline PASSED
backend/tests/test_audit_suite.py::test_6_evidence_verifier_grounding_rules PASSED
backend/tests/test_audit_suite.py::test_7_evidence_verifier_conflicts_detection PASSED
backend/tests/test_audit_suite.py::test_8_knowledge_graph_generation PASSED
backend/tests/test_audit_suite.py::test_9_handover_report_and_approval_workflow PASSED
backend/tests/test_audit_suite.py::test_10_pdf_export_generation PASSED
backend/tests/test_audit_suite.py::test_11_rbac_and_project_isolation PASSED
backend/tests/test_audit_suite.py::test_12_settings_and_audit_logs PASSED
backend/tests/test_audit_suite.py::test_13_employee_passport_and_reconstruction PASSED
backend/tests/test_audit_suite.py::test_14_handover_initiation_and_acknowledgement PASSED
backend/tests/test_audit_suite.py::test_15_source_connection_and_conflicts PASSED
backend/tests/test_audit_suite.py::test_16_ask_project_ai_grounded_rag PASSED

======================= 16 passed in 20.34s =======================
```

---

## 6. Environment Variables (Optional Configuration)

Create a `.env` file in the project root if you want to configure third-party AI keys:

```env
# Server Configuration
PORT=8000
HOST=127.0.0.1
DEBUG=True

# JWT Secret
SECRET_KEY=continuum_super_secret_jwt_signing_key_2025

# Database URL (Default: local SQLite database)
DATABASE_URL=sqlite:///./backend/data/continuum.db

# Vector Database Path
CHROMA_DB_PATH=./backend/data/chroma

# Optional Third-Party LLM API Keys (Default: Local deterministic engine)
OPENAI_API_KEY=
GEMINI_API_KEY=
GITHUB_TOKEN=
```

