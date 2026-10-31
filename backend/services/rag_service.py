"""
RAGService — ChromaDB-backed semantic search for government student schemes.

Embeddings are generated with Google's text-embedding-004 model via the
`google-generativeai` SDK.  The service is designed to be instantiated once
(singleton) and reused across LangGraph nodes.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger("schemepath.rag_service")

# ─── Custom Embedding Function ────────────────────────────────────────────────


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB-compatible embedding function that delegates to Google's
    text-embedding-004 model.
    """

    def __init__(self, task_type: str = "retrieval_document") -> None:
        self._task_type = task_type
        self._genai: Optional[Any] = None
        self._available = False

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning(
                "GOOGLE_API_KEY is not set — GeminiEmbeddingFunction will return "
                "zero-vectors and semantic search will be degraded."
            )
            return

        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=api_key)
            self._genai = genai
            self._available = True
            logger.info("GeminiEmbeddingFunction initialised (task_type=%s).", task_type)
        except ImportError:
            logger.error(
                "google-generativeai package is not installed. "
                "Install it with: pip install google-generativeai"
            )

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        """Embed a batch of text strings."""
        if not self._available or self._genai is None:
            # Fallback: return zero vectors of a fixed dimension
            logger.debug("Returning zero-vectors (embedding unavailable).")
            return [[0.0] * 768 for _ in input]

        embeddings: Embeddings = []
        for text in input:
            try:
                result = self._genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type=self._task_type,
                )
                embeddings.append(result["embedding"])
            except Exception as exc:
                logger.error("Embedding failed for text snippet: %s", exc)
                embeddings.append([0.0] * 768)
        return embeddings


# ─── RAGService ───────────────────────────────────────────────────────────────

_COLLECTION_NAME = "student_schemes"
_PERSIST_DIR = "./data/chromadb"


class RAGService:
    """
    Persistent ChromaDB service for storing and semantically querying student
    government schemes.

    Usage::

        rag = RAGService()
        await rag.add_schemes(scheme_dicts)
        results = await rag.search_schemes("scholarship for OBC girls in Maharashtra")
    """

    def __init__(self) -> None:
        os.makedirs(_PERSIST_DIR, exist_ok=True)

        self._client = chromadb.PersistentClient(path=_PERSIST_DIR)

        self._embed_fn = GeminiEmbeddingFunction(task_type="retrieval_document")
        self._query_embed_fn = GeminiEmbeddingFunction(task_type="retrieval_query")

        # Get-or-create the collection; supply the embedding function so that
        # ChromaDB knows how to embed incoming documents automatically.
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "RAGService ready — collection '%s' has %d documents.",
            _COLLECTION_NAME,
            self._collection.count(),
        )

    # ── Public async API ──────────────────────────────────────────────────────

    async def add_schemes(self, schemes: List[Dict]) -> None:
        """
        Embed and upsert a list of scheme dicts into ChromaDB.

        Each document text is composed of the scheme's name, description, and
        eligibility summary so that semantic queries can match on all three.
        The full scheme dict is stored as JSON in the document metadata for
        later retrieval.
        """
        if not schemes:
            logger.debug("add_schemes called with empty list — nothing to do.")
            return

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict] = []

        for scheme in schemes:
            scheme_id: str = scheme.get("scheme_id") or scheme.get("id") or str(hash(scheme.get("name", "")))
            name: str = scheme.get("name", "")
            description: str = scheme.get("description", "")
            eligibility: str = scheme.get("eligibility_summary", "")

            document_text = f"{name}. {description}. Eligibility: {eligibility}"

            # ChromaDB metadata values must be str | int | float | bool
            # We serialise the full dict to a JSON string and store under "data".
            metadata: Dict[str, Any] = {"data": json.dumps(scheme, ensure_ascii=False)}

            ids.append(scheme_id)
            documents.append(document_text)
            metadatas.append(metadata)

        try:
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info("Upserted %d schemes into ChromaDB collection '%s'.", len(ids), _COLLECTION_NAME)
        except Exception as exc:
            logger.exception("Failed to upsert schemes into ChromaDB: %s", exc)
            raise

    async def search_schemes(self, query: str, n_results: int = 20) -> List[Dict]:
        """
        Perform a semantic similarity search over the stored schemes.

        Returns a list of scheme dicts (deserialised from metadata), ordered by
        descending similarity to *query*.
        """
        total = self._collection.count()
        if total == 0:
            logger.warning("ChromaDB collection is empty — returning no results.")
            return []

        effective_n = min(n_results, total)

        try:
            # Use the query-optimised embedding function for the search vector
            query_embedding: List[float] = self._query_embed_fn([query])[0]

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=effective_n,
                include=["metadatas", "distances"],
            )
        except Exception as exc:
            logger.exception("ChromaDB query failed: %s", exc)
            return []

        scheme_dicts: List[Dict] = []
        metadatas_list = results.get("metadatas") or []
        for batch in metadatas_list:
            for meta in batch:
                raw = meta.get("data")
                if raw:
                    try:
                        scheme_dicts.append(json.loads(raw))
                    except json.JSONDecodeError as json_err:
                        logger.error("Failed to deserialise scheme metadata: %s", json_err)

        logger.info(
            "search_schemes('%s') → %d results (requested %d, available %d).",
            query[:60],
            len(scheme_dicts),
            n_results,
            total,
        )
        return scheme_dicts

    async def clear(self) -> None:
        """Delete all documents from the scheme collection."""
        try:
            self._client.delete_collection(_COLLECTION_NAME)
            # Recreate so the service remains usable
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION_NAME,
                embedding_function=self._embed_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection '%s' cleared and recreated.", _COLLECTION_NAME)
        except Exception as exc:
            logger.exception("Failed to clear ChromaDB collection: %s", exc)
            raise
