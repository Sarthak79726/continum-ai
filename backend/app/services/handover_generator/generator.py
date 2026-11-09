from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.all_models import (
    Project, HandoverReport, Task, Decision, Risk, Dependency,
    ExtractedKnowledge, Evidence, Document, User
)

def build_handover_content(
    db: Session,
    project: Project,
    view_mode: str = "incoming_member_view",
    creator_name: str = "Lead Engineer"
) -> Dict[str, Any]:
    """
    Constructs the 14-section comprehensive handover report content
    from extracted and verified project state.
    """
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    completed_tasks = [t for t in tasks if t.status == "completed"]
    ongoing_tasks = [t for t in tasks if t.status == "in_progress"]
    pending_tasks = [t for t in tasks if t.status in ["pending", "blocked"]]
    recommendations = [t for t in tasks if t.is_recommendation]

    decisions = db.query(Decision).filter(Decision.project_id == project.id).all()
    risks = db.query(Risk).filter(Risk.project_id == project.id).all()
    dependencies = db.query(Dependency).filter(Dependency.project_id == project.id).all()
    evidence_items = db.query(Evidence).filter(Evidence.project_id == project.id).all()
    documents = db.query(Document).filter(Document.project_id == project.id).all()

    # Overview from extracted knowledge
    overview_entry = db.query(ExtractedKnowledge).filter(
        ExtractedKnowledge.project_id == project.id,
        ExtractedKnowledge.category == "overview"
    ).first()

    overview_data = overview_entry.structured_content if overview_entry else {
        "project_purpose": project.description or f"Operational continuity handover for {project.name}",
        "main_objectives": ["Preserve system continuity", "Provide clear technical ramp-up context"],
        "current_development_stage": "Active Development",
        "important_technical_components": ["Core Engine", "Web Client", "API Gateway"]
    }

    questions_entry = db.query(ExtractedKnowledge).filter(
        ExtractedKnowledge.project_id == project.id,
        ExtractedKnowledge.category == "unresolved_questions"
    ).first()
    unresolved_questions = questions_entry.structured_content if questions_entry else []

    # Format 14 Sections
    sections = {
        "metadata": {
            "project_name": project.name,
            "report_title": f"Knowledge Handover & Continuity Dossier — {project.name}",
            "generated_at": datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC"),
            "view_mode": view_mode,
            "created_by": creator_name,
            "status": "draft"
        },
        "1_project_overview": {
            "title": "1. Project Overview",
            "purpose": overview_data.get("project_purpose", project.description),
            "stage": overview_data.get("current_development_stage", "Active Development")
        },
        "2_project_objectives": {
            "title": "2. Project Objectives",
            "objectives": overview_data.get("main_objectives", [])
        },
        "3_team_responsibilities": {
            "title": "3. Team & Ownership Map",
            "roles": [
                {"role": "Outgoing Developer", "name": "Rahul", "responsibility": "Authentication, Payment Gateway API, Database Setup"},
                {"role": "Incoming Member", "name": "Successor Engineer", "responsibility": "Complete Payment Sandbox Integration & Testing"},
                {"role": "Project Owner", "name": project.owner.name if project.owner else "Admin", "responsibility": "Sprint Review & Architecture Sign-off"}
            ]
        },
        "4_completed_work": {
            "title": "4. Completed Work & Verified Milestones",
            "items": [{
                "title": t.title,
                "description": t.description,
                "owner": t.owner,
                "source": t.source_reference
            } for t in completed_tasks]
        },
        "5_ongoing_work": {
            "title": "5. Ongoing Work & Current Sprints",
            "items": [{
                "title": t.title,
                "description": t.description,
                "owner": t.owner,
                "priority": t.priority
            } for t in ongoing_tasks]
        },
        "6_pending_tasks": {
            "title": "6. Pending Tasks & Backlog",
            "items": [{
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "owner": t.owner
            } for t in pending_tasks if not t.is_recommendation]
        },
        "7_important_decisions": {
            "title": "7. Architectural & Design Decisions",
            "items": [{
                "title": d.title,
                "description": d.description,
                "reasoning": d.reasoning,
                "date": d.date_decided,
                "source": d.source_reference
            } for d in decisions]
        },
        "8_technical_architecture": {
            "title": "8. Technical Architecture Summary",
            "components": overview_data.get("important_technical_components", []),
            "stack_summary": "FastAPI, React TypeScript, SQLite/PostgreSQL, ChromaDB semantic vector index, JWT Auth."
        },
        "9_risks_and_blockers": {
            "title": "9. Critical Risks & Blockers",
            "items": [{
                "title": r.title,
                "description": r.description,
                "severity": r.severity,
                "resolution": r.suggested_resolution
            } for r in risks]
        },
        "10_dependencies": {
            "title": "10. Task & System Dependencies",
            "items": [{
                "source": dep.source_title,
                "target": dep.target_title,
                "explanation": dep.description
            } for dep in dependencies]
        },
        "11_unresolved_questions": {
            "title": "11. Unresolved Questions & Contradictions",
            "items": unresolved_questions
        },
        "12_recommended_next_actions": {
            "title": "12. Continuity Blueprint — Actionable Next Steps",
            "items": [t.title for t in recommendations] if recommendations else [
                "Obtain payment gateway sandbox credentials from finance department",
                "Complete webhook payment callback validation logic",
                "Execute end-to-end user signup and checkout test suite"
            ]
        },
        "13_supporting_evidence": {
            "title": "13. Supporting Evidence Passport",
            "items": [{
                "claim": ev.claim_text,
                "snippet": ev.source_snippet,
                "document": ev.document.filename if ev.document else "Project Document",
                "page": ev.page_number,
                "status": ev.verification_status,
                "quality": ev.quality_label
            } for ev in evidence_items[:12]]
        },
        "14_source_documents": {
            "title": "14. Source Document Registry",
            "documents": [{
                "filename": doc.filename,
                "type": doc.file_type.upper(),
                "status": doc.processing_status,
                "chunks": len(doc.chunks)
            } for doc in documents]
        }
    }

    return sections

