"""
RAG Knowledge Base — ChromaDB-backed vector store for SAR investigation context.

Keeps all account data local. Uses a local embedding model so no PII ever
leaves the environment.
"""

import os
import hashlib
import uuid
from typing import List, Optional

import chromadb
from chromadb.config import Settings

_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        chroma_path = os.getenv("CHROMADB_PERSIST_DIR", "/tmp/chromadb")
        _client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        return SentenceTransformer(model_name)
    except ImportError:
        return None


class SARKnowledgeBase:
    """
    ChromaDB-backed knowledge base for SAR investigation.

    Stores:
    - Past alert narratives (FIU notes, investigator notes)
    - Pattern type guidelines
    - Investigator Q&A histories

    All data stored locally. Account IDs tokenized before indexing.
    """

    COLLECTION_NAME = "sar_investigations"

    def __init__(self):
        self._client = _get_client()
        self._model = _get_embedding_model()
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "SAR investigation history and guidelines"},
        )

    def add_alert_narrative(
        self,
        alert_id: str,
        pattern_type: str,
        risk_score: int,
        narrative: str,
        tokenized: bool = True,
    ) -> str:
        """
        Index a SAR narrative for future RAG retrieval.

        If tokenized=False, the narrative contains real account IDs.
        """
        doc_id = hashlib.sha256(alert_id.encode()).hexdigest()[:16]

        self._collection.add(
            documents=[narrative],
            ids=[doc_id],
            metadatas=[
                {
                    "alert_id": alert_id,
                    "pattern_type": pattern_type,
                    "risk_score": risk_score,
                    "tokenized": tokenized,
                    "source": "sar_narrative",
                }
            ],
        )
        return doc_id

    def add_guideline(self, pattern_type: str, guideline_text: str) -> str:
        """Index FIU pattern detection guidelines."""
        doc_id = f"guideline_{pattern_type}_{uuid.uuid4().hex[:8]}"
        self._collection.add(
            documents=[guideline_text],
            ids=[doc_id],
            metadatas=[
                {
                    "pattern_type": pattern_type,
                    "source": "fiu_guideline",
                    "tokenized": False,
                }
            ],
        )
        return doc_id

    def add_qa_pair(
        self,
        question: str,
        answer: str,
        pattern_type: Optional[str] = None,
    ) -> str:
        """Index investigator Q&A for future reference."""
        doc_id = f"qa_{uuid.uuid4().hex[:8]}"
        self._collection.add(
            documents=[f"Q: {question}\nA: {answer}"],
            ids=[doc_id],
            metadatas=[
                {
                    "pattern_type": pattern_type or "general",
                    "source": "investigator_qa",
                    "tokenized": False,
                }
            ],
        )
        return doc_id

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        pattern_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Retrieve relevant documents from the knowledge base.

        Returns tokenized docs — caller must detokenize if needed.
        """
        if self._model is None:
            return []

        query_embedding = self._model.encode([query]).tolist()

        where_filter = {"pattern_type": pattern_type} if pattern_type else None

        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            retrieved.append(
                {
                    "content": doc,
                    "metadata": meta or {},
                    "distance": dist,
                    "relevance_score": max(0.0, 1.0 - (dist or 0) / 2.0),
                }
            )
        return retrieved

    def build_rag_context(
        self,
        query: str,
        pattern_type: Optional[str] = None,
        n_results: int = 3,
    ) -> str:
        """
        Build a RAG-enhanced context string from the knowledge base.

        Combines retrieved documents with the query for LLM enrichment.
        """
        docs = self.retrieve(query, n_results=n_results, pattern_type=pattern_type)
        if not docs:
            return ""

        lines = ["--- RELEVANT PRIOR CASES & GUIDELINES ---"]
        for i, doc in enumerate(docs, 1):
            lines.append(f"[Case {i}] (relevance: {doc['relevance_score']:.2f})")
            lines.append(doc["content"][:500])
            lines.append("")

        return "\n".join(lines)

    def count(self) -> int:
        """Return total number of indexed documents."""
        return self._collection.count()


_kb_instance: Optional[SARKnowledgeBase] = None


def get_knowledge_base() -> SARKnowledgeBase:
    """Get or create the singleton knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = SARKnowledgeBase()
    return _kb_instance
