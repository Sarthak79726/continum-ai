import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.embeddings.embedding_service import get_embedding_function

class ChromaVectorStore:
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = get_embedding_function()

    def get_collection_name(self, project_id: int) -> str:
        return f"continuum_proj_{project_id}"

    def get_or_create_collection(self, project_id: int):
        col_name = self.get_collection_name(project_id)
        return self.client.get_or_create_collection(
            name=col_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        project_id: int,
        chunks: List[Dict[str, Any]]
    ):
        """
        chunks: List of dicts with:
        id: str
        text: str
        document_id: int
        filename: str
        page_number: int
        chunk_index: int
        """
        if not chunks:
            return

        collection = self.get_or_create_collection(project_id)
        
        ids = [str(c["id"]) for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{
            "document_id": int(c["document_id"]),
            "filename": str(c.get("filename", "unknown")),
            "page_number": int(c.get("page_number") or 1),
            "chunk_index": int(c.get("chunk_index", 0)),
            "project_id": int(project_id)
        } for c in chunks]

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self,
        project_id: int,
        query: str,
        n_results: int = 6,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(project_id)
        count = collection.count()
        if count == 0:
            return []

        limit = min(n_results, count)
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter
        )

        hits: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return hits

        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            text = results["documents"][0][i] if results.get("documents") else ""
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            dist = results["distances"][0][i] if results.get("distances") else 0.0

            hits.append({
                "chunk_id": doc_id,
                "text": text,
                "metadata": meta,
                "score": float(1.0 - dist) if dist is not None else 1.0
            })

        return hits

    def delete_document_chunks(self, project_id: int, document_id: int):
        try:
            collection = self.get_or_create_collection(project_id)
            collection.delete(where={"document_id": int(document_id)})
        except Exception:
            pass

    def delete_project_collection(self, project_id: int):
        col_name = self.get_collection_name(project_id)
        try:
            self.client.delete_collection(col_name)
        except Exception:
            pass

# Global vector store instance
vector_store = ChromaVectorStore()

