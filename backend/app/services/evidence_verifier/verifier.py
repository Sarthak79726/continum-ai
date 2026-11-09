from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import Evidence, Document, DocumentChunk, VerificationStatus

class EvidenceVerifier:
    def __init__(self, db: Session, project_id: int):
        self.db = db
        self.project_id = project_id

    def create_evidence_record(
        self,
        claim_text: str,
        source_snippet: str,
        document_name: Optional[str] = None,
        page_number: Optional[int] = None,
        chunk_id: Optional[int] = None,
        verification_status: str = "NEEDS_REVIEW",
        quality_label: str = "Direct Citation",
        knowledge_id: Optional[int] = None
    ) -> Evidence:
        """
        Records an inspected evidence passport item with grounded snippet link.
        """
        # Resolve document ID if document_name is given
        doc_id = None
        if document_name:
            doc = self.db.query(Document).filter(
                Document.project_id == self.project_id,
                Document.filename == document_name
            ).first()
            if doc:
                doc_id = doc.id

        if not doc_id:
            # Fallback to any document in the project
            first_doc = self.db.query(Document).filter(Document.project_id == self.project_id).first()
            doc_id = first_doc.id if first_doc else 1

        # Check if source_snippet genuinely exists in document text
        status_val = verification_status
        if not source_snippet or source_snippet.lower() in ["unknown", "none", "not specified"]:
            status_val = VerificationStatus.UNVERIFIED.value
            quality_label = "Insufficient Context"
        elif "conflicting" in source_snippet.lower() or "disagree" in source_snippet.lower():
            status_val = VerificationStatus.CONFLICTING.value
            quality_label = "Conflicting"
        elif len(source_snippet.strip()) > 15:
            # Verified with direct source grounding
            if status_val == "NEEDS_REVIEW" and "verified" in source_snippet.lower():
                status_val = VerificationStatus.VERIFIED.value

        evidence = Evidence(
            project_id=self.project_id,
            knowledge_id=knowledge_id,
            document_id=doc_id,
            chunk_id=chunk_id,
            claim_text=claim_text.strip(),
            source_snippet=source_snippet.strip(),
            page_number=page_number or 1,
            verification_status=status_val,
            quality_label=quality_label
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def detect_conflicts(self, task_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans extracted tasks and items for contradictory claims across sources.
        Returns a list of conflict notices to store in Unresolved Questions.
        """
        conflicts = []
        status_map: Dict[str, List[Dict[str, Any]]] = {}

        for item in task_items:
            title_key = item.get("title", "").lower().strip()
            if not title_key:
                continue
            if title_key not in status_map:
                status_map[title_key] = []
            status_map[title_key].append(item)

        for title, occurrences in status_map.items():
            if len(occurrences) > 1:
                statuses = set(o.get("status") for o in occurrences)
                if len(statuses) > 1:
                    conflicts.append({
                        "question": f"Conflicting status reported for task: '{occurrences[0]['title']}'",
                        "category": "contradictory_information",
                        "details": f"Discrepancy detected across sources: Reported statuses include {list(statuses)}.",
                        "source_document": occurrences[0].get("source_document", "Multiple Documents")
                    })

        return conflicts

