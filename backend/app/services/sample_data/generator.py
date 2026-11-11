import os
import io
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import pandas as pd
import docx
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.models.all_models import (
    Project, Document, DocumentChunk, ExtractedKnowledge,
    Task, Decision, Risk, Dependency, Evidence, User, UserRole,
    VerificationStatus, TaskStatus, PriorityLevel, EmployeeProfile,
    HandoverLifecycleStatus, APIEndpointRecord
)
from app.services.vector_store.chroma_service import vector_store

SAMPLE_DOCS_DIR = "./data/sample_documents"

def generate_sample_files_on_disk():
    os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)

    # 1. project_overview.pdf
    pdf_path = os.path.join(SAMPLE_DOCS_DIR, "project_overview.pdf")
    if not os.path.exists(pdf_path):
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("SMART CAMPUS MANAGEMENT SYSTEM - PROJECT ARCHITECTURE OVERVIEW", styles['Title']),
            Spacer(1, 12),
            Paragraph("Lead Outgoing Developer: Rahul (Department of Computer Engineering)", styles['Normal']),
            Paragraph("Project Status: Active Integration Sprint 4 | Stage: Pre-Release Handover", styles['Normal']),
            Spacer(1, 14),
            Paragraph("1. System Purpose & Scope:", styles['Heading2']),
            Paragraph("The Smart Campus Management System unifies student authentication, course enrollments, automated campus fees collection, and administrative operations into a single secure platform.", styles['Normal']),
            Spacer(1, 10),
            Paragraph("2. Implemented Modules:", styles['Heading2']),
            Paragraph("• Student & Staff Authentication Module: Fully completed using FastAPI JWT bearer tokens, bcrypt password hashing, and role-based permissions.", styles['Normal']),
            Paragraph("• Core PostgreSQL/SQLite schema migrations: User profiles, campus departments, and access tiers completed.", styles['Normal']),
            Spacer(1, 10),
            Paragraph("3. In-Progress & Blocked Components:", styles['Heading2']),
            Paragraph("• Payment Gateway API: Incomplete. Webhook verification logic is drafted, but live gateway sandbox credentials are still awaited from the finance office.", styles['Normal']),
            Paragraph("• Password Reset Feature: Pending frontend modal connection and SMTP mail service credentials.", styles['Normal']),
        ]
        doc.build(story)

    # 2. meeting_notes.txt
    txt_path = os.path.join(SAMPLE_DOCS_DIR, "meeting_notes.txt")
    if not os.path.exists(txt_path):
        content = """CAMPUS TECH SPRINT RETROSPECTIVE & HANDOVER MEETING NOTES
Date: October 24, 2025
Attendees: Rahul (Lead Developer), Sarah (Product Manager), Alex (Frontend Engineer)

Key Discussion Points:
1. Authentication module sign-off:
   Rahul demonstrated user login and signup. The JWT validation has been thoroughly verified across all protected endpoints.
   Decision: Approved for production staging.

2. Payment Integration Blocker:
   Rahul reported that payment integration is currently blocked. The payment gateway sandbox credentials have not been released by the Bursar's office.
   Quote from Rahul: "We cannot test simulated credit card or UPI transactions until the finance department provides merchant test keys."
   Action item: Sarah to follow up with campus finance director.

3. Architecture Decisions:
   - Rahul chose SQLite for local rapid prototyping and tests, designed with SQLAlchemy 2.0 to ensure zero-friction migration to PostgreSQL in production.
   - Decided to adopt ChromaDB for campus directory semantic search over FAISS for simpler embedded lifecycle.

4. Known Unresolved Questions:
   - Who will manage the production SMTP server keys once Rahul departs on Friday?
   - Contradiction noted: Sprint task board lists Password Recovery as 'Ready for QA', but backend documentation clearly shows email dispatch service is not yet configured.
"""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. task_status.csv
    csv_path = os.path.join(SAMPLE_DOCS_DIR, "task_status.csv")
    if not os.path.exists(csv_path):
        df = pd.DataFrame([
            {"Task ID": "TSK-101", "Module": "Authentication", "Title": "JWT Token Auth & RBAC", "Status": "Completed", "Owner": "Rahul", "Priority": "Critical", "Evidence Reference": "Verified in test suite and postman collection"},
            {"Task ID": "TSK-102", "Module": "Payment", "Title": "Payment Gateway API Integration", "Status": "Blocked", "Owner": "Rahul", "Priority": "Critical", "Evidence Reference": "Awaiting merchant sandbox credentials"},
            {"Task ID": "TSK-103", "Module": "Auth", "Title": "Password Recovery & Reset Modal", "Status": "Pending", "Owner": "Alex", "Priority": "High", "Evidence Reference": "Blocked by missing SMTP email credentials"},
            {"Task ID": "TSK-104", "Module": "Database", "Title": "SQLite to Postgres Schema Migration Script", "Status": "Completed", "Owner": "Rahul", "Priority": "Medium", "Evidence Reference": "SQLAlchemy alembic models validated"},
            {"Task ID": "TSK-105", "Module": "Frontend", "Title": "Campus Dashboard Analytics View", "Status": "In Progress", "Owner": "Sarah", "Priority": "Medium", "Evidence Reference": "Recharts visual components in development"},
            {"Task ID": "TSK-106", "Module": "Security", "Title": "Annual Student Data Privacy Audit", "Status": "Pending", "Owner": "Rahul", "Priority": "High", "Evidence Reference": "Scheduled before term start"}
        ])
        df.to_csv(csv_path, index=False)

    # 4. technical_updates.docx
    docx_path = os.path.join(SAMPLE_DOCS_DIR, "technical_updates.docx")
    if not os.path.exists(docx_path):
        doc = docx.Document()
        doc.add_heading("Smart Campus System - Technical Architecture & Dependency Brief", 0)
        doc.add_paragraph("Author: Rahul (Outgoing Developer) | Handover Recipient: Incoming Software Engineer")
        
        doc.add_heading("1. Critical Architecture Dependencies", level=1)
        doc.add_paragraph("• Payment API Integration directly depends on Gateway Sandbox Credentials.")
        doc.add_paragraph("• Frontend Payment Checkout UI directly depends on Payment API Integration.")
        doc.add_paragraph("• Password Recovery Dispatch depends on Campus SMTP Server Access.")

        doc.add_heading("2. Identified Technical Risks & Bottlenecks", level=1)
        doc.add_paragraph("Risk Alpha: The payment gateway webhook receiver lacks replay-attack nonce verification. Suggested Resolution: Implement timestamp and SHA-256 HMAC payload verification before processing receipt callback.")
        doc.add_paragraph("Risk Beta: Departure of primary architect without documented production environment keys. Impact: Deployment delay of 2-3 weeks if credentials are lost.")

        doc.add_heading("3. Handover Advice for Rahul's Successor", level=1)
        doc.add_paragraph("First week priority: 1) Secure the payment credentials from Sarah. 2) Run the local test suite using 'pytest'. 3) Verify that password recovery email templating works in staging.")

        doc.save(docx_path)

def load_sample_dataset(db: Session, user: User) -> Project:
    """
    Creates the synthetic SMART CAMPUS MANAGEMENT SYSTEM demo project,
    loads the 4 demo documents, chunks them, indexes in ChromaDB,
    and runs initial structured knowledge population.
    """
    generate_sample_files_on_disk()

    # Check if demo project already exists for this user
    existing_project = db.query(Project).filter(
        Project.owner_id == user.id,
        Project.name == "Smart Campus Management System (DEMO)"
    ).first()

    if existing_project:
        emp_count = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == existing_project.id).count()
        if emp_count > 0:
            apis_count = db.query(APIEndpointRecord).filter(APIEndpointRecord.project_id == existing_project.id).count()
            if apis_count == 0:
                rahul = db.query(EmployeeProfile).filter(EmployeeProfile.project_id == existing_project.id, EmployeeProfile.name.ilike("%Rahul%")).first()
                if rahul:
                    from app.services.sources.github_service import github_service
                    from app.services.employee_passport.passport_service import passport_service
                    mapping = {e.name: e.id for e in db.query(EmployeeProfile).filter(EmployeeProfile.project_id == existing_project.id).all()}
                    github_service.sync_repository_to_db(existing_project.id, "continuum-campus", "smart-campus-core", db, mapping)
                    passport_service.reconstruct_employee_knowledge(rahul.id, db)
            return existing_project
        # Project exists but needs employee roster and passport data seeded
        demo_project = existing_project
    else:
        demo_project = Project(
            name="Smart Campus Management System (DEMO)",
            description="Official synthetic demonstration project for Continuum AI handover platform. Models knowledge transition for departing lead developer Rahul.",
            owner_id=user.id,
            status="active",
            is_demo=True
        )
        db.add(demo_project)
        db.commit()
        db.refresh(demo_project)

    # Create Document records and chunks
    sample_files = [
        ("project_overview.pdf", "pdf"),
        ("meeting_notes.txt", "txt"),
        ("task_status.csv", "csv"),
        ("technical_updates.docx", "docx")
    ]

    from app.services.document_processor.pipeline import process_document_file

    all_chunks_to_index = []

    for filename, file_type in sample_files:
        path = os.path.join(SAMPLE_DOCS_DIR, filename)
        if not os.path.exists(path):
            continue

        file_size = os.path.getsize(path)
        doc_record = Document(
            project_id=demo_project.id,
            uploaded_by=user.id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=path,
            processing_status="processed"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        chunks_data = process_document_file(path, file_type)
        for c in chunks_data:
            chunk_record = DocumentChunk(
                document_id=doc_record.id,
                project_id=demo_project.id,
                chunk_index=c["chunk_index"],
                page_number=c.get("page_number", 1),
                section_title=c.get("section_title"),
                extracted_text=c["text"],
                token_count=c.get("token_count", 0)
            )
            db.add(chunk_record)
            db.commit()
            db.refresh(chunk_record)

            all_chunks_to_index.append({
                "id": str(chunk_record.id),
                "text": chunk_record.extracted_text,
                "document_id": doc_record.id,
                "filename": filename,
                "page_number": chunk_record.page_number,
                "chunk_index": chunk_record.chunk_index
            })

    # Index in ChromaDB
    vector_store.add_chunks(demo_project.id, all_chunks_to_index)

    # Run AI Knowledge Reconstruction
    from app.services.knowledge_extractor.extractor import KnowledgeExtractor
    extractor = KnowledgeExtractor(db, demo_project)
    extractor.run_reconstruction(user.id)

    # Seed Hackathon Multi-Employee Roster
    from app.services.sources.github_service import github_service
    from app.services.employee_passport.passport_service import passport_service

    # 1. Maya Patel (Successor - Incoming Backend Developer)
    maya = EmployeeProfile(
        project_id=demo_project.id,
        name="Maya Patel",
        employee_id_code="EMP-104",
        role_title="Incoming Backend Developer",
        department="Engineering",
        responsibilities=["Backend API Maintenance", "Payment Gateway Completion", "Database Schema Evolution"],
        date_joined="2025-10-25",
        handover_status=HandoverLifecycleStatus.ACTIVE.value,
        last_activity_date="2025-10-25",
        contribution_summary="Incoming successor engineer reviewing handover dossier and continuation checklist."
    )
    db.add(maya)
    db.commit()
    db.refresh(maya)

    # 2. Rahul Sharma (Departing Lead Backend Developer)
    rahul = EmployeeProfile(
        project_id=demo_project.id,
        name="Rahul Sharma",
        employee_id_code="EMP-101",
        role_title="Lead Backend Developer",
        department="Engineering",
        responsibilities=["FastAPI Backend Services", "JWT Authentication", "SQLite/Postgres Database Models", "Stripe Payment Gateway Integration"],
        date_joined="2024-06-01",
        handover_initiation_date="2025-10-24",
        assigned_successor_id=maya.id,
        handover_status=HandoverLifecycleStatus.PENDING_APPROVAL.value,
        last_activity_date="2025-10-24",
        contribution_summary="Designed and implemented the core authentication API, student database schema, and initial payment gateway webhook integration."
    )
    db.add(rahul)

    # 3. Sarah Chen (Product Manager / Frontend Developer)
    sarah = EmployeeProfile(
        project_id=demo_project.id,
        name="Sarah Chen",
        employee_id_code="EMP-102",
        role_title="Product Manager & Frontend Engineer",
        department="Product & Design",
        responsibilities=["Campus Dashboard Analytics", "Requirements Engineering", "Finance Office Liaison", "Sprint Planning"],
        date_joined="2024-05-15",
        handover_status=HandoverLifecycleStatus.ACTIVE.value,
        last_activity_date="2025-10-24",
        contribution_summary="Leads sprint planning, campus dashboard UI development with Recharts, and holds liaison contact with the Bursar finance office."
    )
    db.add(sarah)

    # 4. Alex Kumar (Core System Developer & Architect)
    alex = EmployeeProfile(
        project_id=demo_project.id,
        name="Alex Kumar",
        employee_id_code="EMP-103",
        role_title="Core System Developer & Architect",
        department="Platform Architecture",
        responsibilities=["System Bus Architecture", "Async Event Workers", "Security Code Reviews", "ChromaDB Semantic Search Integration"],
        date_joined="2024-04-10",
        handover_status=HandoverLifecycleStatus.ACTIVE.value,
        last_activity_date="2025-10-24",
        contribution_summary="Architected asynchronous event processing, conducted security code reviews on auth PRs, and configured ChromaDB persistent semantic search."
    )
    db.add(alex)
    db.commit()
    db.refresh(rahul)

    # Sync GitHub commits and PRs attributed to employees
    emp_mapping = {
        "Rahul Sharma": rahul.id,
        "Sarah Chen": sarah.id,
        "Alex Kumar": alex.id,
        "Maya Patel": maya.id
    }
    github_service.sync_repository_to_db(demo_project.id, "continuum-campus", "smart-campus-core", db, emp_mapping)

    # Reconstruct Rahul's complete Knowledge Passport (APIs, schemas, bugs, blockers, knowledge gaps, continuation actions)
    passport_service.reconstruct_employee_knowledge(rahul.id, db)
    rahul.handover_status = HandoverLifecycleStatus.PENDING_APPROVAL.value
    db.commit()

    return demo_project

def purge_sample_dataset(db: Session, user: User) -> bool:
    """
    Removes demo projects and their associated Chroma collections.
    """
    demo_projects = db.query(Project).filter(
        Project.owner_id == user.id,
        Project.is_demo == True
    ).all()

    for p in demo_projects:
        vector_store.delete_project_collection(p.id)
        db.delete(p)
    
    db.commit()
    return True

