import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.document_processor.cleaner import clean_text
from app.services.document_processor.chunker import chunk_document_pages
from app.services.document_processor.pipeline import process_document_file
from app.services.sample_data.generator import generate_sample_files_on_disk
from app.services.handover_generator.pdf_exporter import generate_handover_pdf

client = TestClient(app)

def test_cleaner_and_chunker():
    raw_text = "  First line with  extra   spaces. \n\n\n\n Second line here.  "
    cleaned = clean_text(raw_text)
    assert "First line with extra spaces." in cleaned
    assert "\n\n\n" not in cleaned

    pages = [{"page_number": 1, "text": "This is page 1 content. " * 30}]
    chunks = chunk_document_pages(pages, chunk_size=300, chunk_overlap=50)
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1

def test_sample_files_generation():
    generate_sample_files_on_disk()
    assert os.path.exists("./data/sample_documents/project_overview.pdf")
    assert os.path.exists("./data/sample_documents/meeting_notes.txt")
    assert os.path.exists("./data/sample_documents/task_status.csv")
    assert os.path.exists("./data/sample_documents/technical_updates.docx")

def test_document_parsers():
    generate_sample_files_on_disk()
    # Test TXT
    txt_chunks = process_document_file("./data/sample_documents/meeting_notes.txt", "txt")
    assert len(txt_chunks) >= 1
    assert any("Rahul" in c["text"] for c in txt_chunks)

    # Test CSV
    csv_chunks = process_document_file("./data/sample_documents/task_status.csv", "csv")
    assert len(csv_chunks) >= 1
    assert any("TSK-101" in c["text"] for c in csv_chunks)

    # Test PDF
    pdf_chunks = process_document_file("./data/sample_documents/project_overview.pdf", "pdf")
    assert len(pdf_chunks) >= 1
    assert any("SMART CAMPUS" in c["text"] for c in pdf_chunks)

    # Test DOCX
    docx_chunks = process_document_file("./data/sample_documents/technical_updates.docx", "docx")
    assert len(docx_chunks) >= 1
    assert any("Architecture" in c["text"] for c in docx_chunks)

def test_auth_workflow():
    # Login with default seeded admin
    login_resp = client.post("/api/auth/login", json={
        "email": "demo@continuum.ai",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None

    # Get profile
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "demo@continuum.ai"

    # Register new user
    import uuid
    random_email = f"user_{uuid.uuid4().hex[:6]}@continuum.ai"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Alex Tester",
        "email": random_email,
        "password": "securepassword123",
        "role": "TEAM_MEMBER"
    })
    assert reg_resp.status_code == 201
    assert reg_resp.json()["user"]["email"] == random_email

def test_projects_and_demo_dataset():
    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": "demo@continuum.ai",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Load Demo Data
    demo_resp = client.post("/api/demo/load", headers=headers)
    assert demo_resp.status_code in [200, 201]
    proj_id = demo_resp.json()["project_id"]

    # Verify project exists
    proj_resp = client.get(f"/api/projects/{proj_id}", headers=headers)
    assert proj_resp.status_code == 200
    assert "Smart Campus" in proj_resp.json()["name"]

    # Verify documents exist
    docs_resp = client.get(f"/api/projects/{proj_id}/documents", headers=headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) >= 4

    # Verify Knowledge extraction was populated
    k_resp = client.get(f"/api/projects/{proj_id}/knowledge", headers=headers)
    assert k_resp.status_code == 200
    assert "overview" in k_resp.json()["categories"]

    # Verify Evidence Passport
    ev_resp = client.get(f"/api/projects/{proj_id}/evidence", headers=headers)
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()) >= 1
    assert ev_resp.json()[0]["verification_status"] in ["VERIFIED", "NEEDS_REVIEW", "CONFLICTING", "UNVERIFIED"]

    # Verify Tasks
    tasks_resp = client.get(f"/api/projects/{proj_id}/tasks", headers=headers)
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) >= 1

    # Verify Knowledge Graph
    graph_resp = client.get(f"/api/projects/{proj_id}/graph", headers=headers)
    assert graph_resp.status_code == 200
    assert len(graph_resp.json()["nodes"]) >= 3
    assert len(graph_resp.json()["edges"]) >= 2

    # Verify Handover generation
    handover_resp = client.post(f"/api/projects/{proj_id}/handovers", json={
        "title": "Smart Campus Handover Dossier v1",
        "view_mode": "incoming_member_view"
    }, headers=headers)
    assert handover_resp.status_code == 201
    report_id = handover_resp.json()["id"]

    # Verify Handover PDF export
    pdf_resp = client.get(f"/api/handovers/{report_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000

    # Test Reviewer Approval
    appr_resp = client.post(f"/api/handovers/{report_id}/approve", json={
        "action": "approved",
        "comments": "Inspected and verified against test documents."
    }, headers=headers)
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # Verify Analytics Dashboard
    analytics_resp = client.get("/api/analytics", headers=headers)
    assert analytics_resp.status_code == 200
    assert analytics_resp.json()["total_projects"] >= 1
    assert analytics_resp.json()["documents_processed"] >= 1

