from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.all_models import (
    Project, Document, ExtractedKnowledge, Task, Decision, Risk, Dependency, AuditLog,
    VerificationStatus
)
from app.schemas.all_schemas import ProjectAnalysisPayload
from app.services.retrieval.retriever import ProjectRetriever
from app.services.ai_engine.provider import get_ai_engine
from app.services.evidence_verifier.verifier import EvidenceVerifier

class KnowledgeExtractor:
    def __init__(self, db: Session, project: Project):
        self.db = db
        self.project = project
        self.retriever = ProjectRetriever(db, project.id)
        self.verifier = EvidenceVerifier(db, project.id)
        self.ai_engine = get_ai_engine()

    def run_reconstruction(self, user_id: int) -> Dict[str, Any]:
        """
        Executes end-to-end AI knowledge reconstruction for the project:
        1. Retrieves relevant document chunks
        2. Queries the AI engine with structured prompt
        3. Validates JSON through Pydantic
        4. Detects conflicts and records evidence passport entries
        5. Updates database state
        """
        # 1. Fetch chunks for this project
        chunks = self.retriever.retrieve_relevant_chunks(
            query=f"project purpose objectives completed ongoing pending tasks architecture decisions risks dependencies for {self.project.name}",
            top_k=15
        )
        
        context_str = self.retriever.format_context_for_prompt(chunks)

        # 2. Query AI Engine
        raw_result = self.ai_engine.generate_structured_reconstruction(
            context=context_str,
            project_name=self.project.name,
            chunks=chunks
        )

        # 3. Validate against Pydantic schema
        validated_payload = ProjectAnalysisPayload(**raw_result)

        # 4. Check for cross-source conflicts
        all_task_items = [t.model_dump() for t in validated_payload.completed_tasks + validated_payload.ongoing_tasks + validated_payload.pending_tasks]
        conflicts = self.verifier.detect_conflicts(all_task_items)
        if conflicts:
            for conf in conflicts:
                validated_payload.unresolved_questions.append(conf)

        # 5. Clear old extracted records for this project to keep state clean & current
        self.db.query(Task).filter(Task.project_id == self.project.id).delete()
        self.db.query(Decision).filter(Decision.project_id == self.project.id).delete()
        self.db.query(Risk).filter(Risk.project_id == self.project.id).delete()
        self.db.query(Dependency).filter(Dependency.project_id == self.project.id).delete()
        self.db.query(ExtractedKnowledge).filter(ExtractedKnowledge.project_id == self.project.id).delete()
        self.db.commit()

        # 6. Save ExtractedKnowledge records
        for category_name, content in validated_payload.model_dump().items():
            k_record = ExtractedKnowledge(
                project_id=self.project.id,
                category=category_name,
                structured_content=content,
                verification_status=VerificationStatus.VERIFIED.value if category_name == "overview" else VerificationStatus.NEEDS_REVIEW.value
            )
            self.db.add(k_record)
        self.db.commit()

        # 7. Populate Tasks & Evidence
        for t in validated_payload.completed_tasks:
            ev = self.verifier.create_evidence_record(
                claim_text=f"Task completed: {t.title}",
                source_snippet=t.completion_evidence or t.description or "Verified in project records",
                document_name=t.source_document,
                page_number=t.page_number,
                verification_status=VerificationStatus.VERIFIED.value,
                quality_label="Direct Citation"
            )
            db_task = Task(
                project_id=self.project.id,
                title=t.title,
                description=t.description,
                status="completed",
                priority="high",
                owner=t.owner or "Unknown",
                source_reference=t.source_document,
                evidence_id=ev.id,
                is_recommendation=False
            )
            self.db.add(db_task)

        for t in validated_payload.ongoing_tasks:
            ev = self.verifier.create_evidence_record(
                claim_text=f"Task in progress: {t.title}",
                source_snippet=t.completion_evidence or t.description or "In progress per recent updates",
                document_name=t.source_document,
                page_number=t.page_number,
                verification_status=VerificationStatus.NEEDS_REVIEW.value,
                quality_label="Inferred"
            )
            db_task = Task(
                project_id=self.project.id,
                title=t.title,
                description=t.description,
                status="in_progress",
                priority="medium",
                owner=t.owner or "Unknown",
                source_reference=t.source_document,
                evidence_id=ev.id,
                is_recommendation=False
            )
            self.db.add(db_task)

        for t in validated_payload.pending_tasks:
            ev = self.verifier.create_evidence_record(
                claim_text=f"Task pending / blocked: {t.title}",
                source_snippet=t.completion_evidence or t.description or "Pending or blocked in backlog",
                document_name=t.source_document,
                page_number=t.page_number,
                verification_status=VerificationStatus.NEEDS_REVIEW.value,
                quality_label="Direct Citation"
            )
            db_task = Task(
                project_id=self.project.id,
                title=t.title,
                description=t.description,
                status="pending",
                priority="critical" if "credential" in t.title.lower() or "payment" in t.title.lower() else "high",
                owner=t.owner or "Unknown",
                source_reference=t.source_document,
                evidence_id=ev.id,
                is_recommendation=False
            )
            self.db.add(db_task)

        # Also add recommendations as actionable continuation items
        for rec in validated_payload.recommended_next_actions:
            db_task = Task(
                project_id=self.project.id,
                title=rec.split(". ")[-1] if ". " in rec else rec,
                description="Continuity Blueprint Recommended Action for incoming team member",
                status="pending",
                priority="critical" if "credential" in rec.lower() or "1." in rec else "high",
                owner="Incoming Engineer",
                source_reference="Continuum AI Continuity Blueprint",
                is_recommendation=True
            )
            self.db.add(db_task)

        # 8. Populate Decisions
        for d in validated_payload.important_decisions:
            db_dec = Decision(
                project_id=self.project.id,
                title=d.title,
                description=d.description,
                reasoning=d.reasoning,
                date_decided=d.date_decided,
                source_reference=d.source_document
            )
            self.db.add(db_dec)
            if d.evidence_snippet:
                self.verifier.create_evidence_record(
                    claim_text=f"Architecture Decision: {d.title}",
                    source_snippet=d.evidence_snippet,
                    document_name=d.source_document,
                    verification_status=VerificationStatus.VERIFIED.value,
                    quality_label="Direct Citation"
                )

        # 9. Populate Risks
        for r in validated_payload.risks_and_blockers:
            db_risk = Risk(
                project_id=self.project.id,
                title=r.title,
                description=r.description,
                severity=r.severity,
                status="active",
                impact=r.potential_impact,
                suggested_resolution=r.suggested_resolution,
                source_reference=r.source_document
            )
            self.db.add(db_risk)
            if r.evidence_snippet:
                self.verifier.create_evidence_record(
                    claim_text=f"Identified Risk: {r.title}",
                    source_snippet=r.evidence_snippet,
                    document_name=r.source_document,
                    verification_status=VerificationStatus.NEEDS_REVIEW.value,
                    quality_label="Direct Citation"
                )

        # 10. Populate Dependencies
        for dep in validated_payload.dependencies:
            db_dep = Dependency(
                project_id=self.project.id,
                source_title=dep.source_title,
                target_title=dep.target_title,
                description=dep.dependency_explanation,
                evidence=dep.evidence_snippet
            )
            self.db.add(db_dep)

        # 11. Record Audit Log
        audit = AuditLog(
            user_id=user_id,
            project_id=self.project.id,
            action="AI_KNOWLEDGE_RECONSTRUCTION",
            details=f"Analyzed {len(chunks)} chunks, reconstructed tasks, decisions, risks, and evidence passport."
        )
        self.db.add(audit)
        self.db.commit()

        return validated_payload.model_dump()

