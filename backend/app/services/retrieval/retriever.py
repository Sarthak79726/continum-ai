from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.vector_store.chroma_service import vector_store
from app.models.all_models import DocumentChunk, Document

class ProjectRetriever:
    def __init__(self, db: Session, project_id: int):
        self.db = db
        self.project_id = project_id

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant chunks using vector search,
        then hydrates with full document metadata from SQL database.
        """
        vector_hits = vector_store.search(
            project_id=self.project_id,
            query=query,
            n_results=top_k
        )

        results: List[Dict[str, Any]] = []
        for hit in vector_hits:
            chunk_id_str = hit["chunk_id"]
            try:
                chunk_id_int = int(chunk_id_str)
                chunk_record = self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id_int).first()
                if chunk_record:
                    doc = self.db.query(Document).filter(Document.id == chunk_record.document_id).first()
                    results.append({
                        "chunk_id": chunk_record.id,
                        "document_id": chunk_record.document_id,
                        "document_name": doc.filename if doc else hit["metadata"].get("filename", "Unknown Doc"),
                        "page_number": chunk_record.page_number,
                        "text": chunk_record.extracted_text,
                        "score": hit["score"]
                    })
                else:
                    results.append({
                        "chunk_id": chunk_id_str,
                        "document_id": hit["metadata"].get("document_id"),
                        "document_name": hit["metadata"].get("filename", "Unknown Doc"),
                        "page_number": hit["metadata"].get("page_number", 1),
                        "text": hit["text"],
                        "score": hit["score"]
                    })
            except Exception:
                results.append({
                    "chunk_id": chunk_id_str,
                    "document_id": hit["metadata"].get("document_id"),
                    "document_name": hit["metadata"].get("filename", "Unknown Doc"),
                    "page_number": hit["metadata"].get("page_number", 1),
                    "text": hit["text"],
                    "score": hit["score"]
                })

        # Fallback: if vector search returned nothing (e.g. index empty or new),
        # retrieve recent chunks directly from DB
        if not results:
            db_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.project_id == self.project_id
            ).limit(top_k).all()
            for c in db_chunks:
                doc = self.db.query(Document).filter(Document.id == c.document_id).first()
                results.append({
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "document_name": doc.filename if doc else "Document",
                    "page_number": c.page_number,
                    "text": c.extracted_text,
                    "score": 0.8
                })

        return results

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats chunks into structured, citation-friendly context block.
        """
        if not chunks:
            return "No project documents available."

        context_parts = []
        for i, c in enumerate(chunks):
            doc_name = c.get("document_name", "Unknown")
            page = c.get("page_number", 1)
            cid = c.get("chunk_id", i)
            text = c.get("text", "").strip()
            context_parts.append(
                f"--- SOURCE REF [{i+1}] (Doc: '{doc_name}', Page: {page}, Chunk ID: {cid}) ---\n{text}\n"
            )

        return "\n".join(context_parts)

