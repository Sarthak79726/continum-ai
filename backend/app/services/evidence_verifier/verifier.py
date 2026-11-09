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
        Strictly guarantees that unsupported claims are never marked VERIFIED.
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
            first_doc = self.db.query(Document).filter(Document.project_id == self.project_id).first()
            if first_doc:
                doc_id = first_doc.id

        if not doc_id:
            raise ValueError(f"Cannot link evidence for project {self.project_id}: No source documents exist.")

        # Grounding verification: Check if snippet exists in project document chunks
        snippet_clean = source_snippet.strip() if source_snippet else ""
        is_grounded = False
        
        if snippet_clean and len(snippet_clean) >= 10:
            # Check if a 25-char key phrase exists in any chunk
            search_prefix = snippet_clean[:35].lower()
            candidate_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.project_id == self.project_id
            ).all()
            for c in candidate_chunks:
                if search_prefix in c.extracted_text.lower():
                    is_grounded = True
                    if not chunk_id:
                        chunk_id = c.id
                    if not page_number and c.page_number:
                        page_number = c.page_number
                    break

        # Verification Status Determination
        status_val = verification_status
        label_val = quality_label

        if not snippet_clean or snippet_clean.lower() in ["unknown", "none", "not specified", "unverified"]:
            status_val = VerificationStatus.UNVERIFIED.value
            label_val = "Insufficient Context"
        elif "conflicting" in snippet_clean.lower() or "disagree" in snippet_clean.lower() or "discrepancy" in snippet_clean.lower():
            status_val = VerificationStatus.CONFLICTING.value
            label_val = "Conflicting Evidence"
        elif not is_grounded:
            # Rule: NEVER mark unsupported claim as VERIFIED
            if status_val == VerificationStatus.VERIFIED.value:
                status_val = VerificationStatus.NEEDS_REVIEW.value
                label_val = "Inferred (Pending Human Verification)"
            elif status_val != VerificationStatus.CONFLICTING.value:
                status_val = VerificationStatus.UNVERIFIED.value
                label_val = "Ungrounded Citation"
        else:
            # Genuinely grounded in document text
            if status_val == "NEEDS_REVIEW" and ("verified" in snippet_clean.lower() or "completed" in claim_text.lower()):
                status_val = VerificationStatus.VERIFIED.value
                label_val = "Direct Grounded Citation"

        evidence = Evidence(
            project_id=self.project_id,
            knowledge_id=knowledge_id,
            document_id=doc_id,
            chunk_id=chunk_id,
            claim_text=claim_text.strip(),
            source_snippet=snippet_clean,
            page_number=page_number or 1,
            verification_status=status_val,
            quality_label=label_val
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
                statuses = set(o.get("status") for o in occurrences if o.get("status"))
                if len(statuses) > 1:
                    conflicts.append({
                        "question": f"Contradiction detected: Task '{occurrences[0]['title']}' reported with conflicting statuses {list(statuses)} across documents.",
                        "category": "contradictory_information",
                        "details": f"Discrepancy identified between {occurrences[0].get('source_document', 'Doc A')} and {occurrences[-1].get('source_document', 'Doc B')}.",
                        "source_document": occurrences[0].get("source_document", "Multiple Documents")
                    })

        return conflicts
