"""
OSMOS Agent Knowledge Base — Repository (Phase 8.5)
===================================================
Database persistence repository for knowledge documents, chunks, and index stats.

Read-Only Guarantee: Modifies ONLY knowledge_documents and knowledge_chunks.
Never modifies customer entity or profile tables.
"""

import logging
from typing import Any, Dict, List, Optional
import psycopg2.extras

from storage.storage_manager import get_storage_backend
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_KNOWLEDGE_REPOSITORY")

_knowledge_tables_checked = False
_in_memory_docs: List[Dict[str, Any]] = []
_in_memory_chunks: List[Dict[str, Any]] = []


def is_knowledge_db_available() -> bool:
    """Checks if PostgreSQL is active and auto-provisions knowledge tables if needed."""
    global _knowledge_tables_checked
    if get_storage_backend() != "postgres" or not is_postgres_available():
        return False

    if _knowledge_tables_checked:
        return True

    try:
        from database.db import get_cursor
        with get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    document_id SERIAL PRIMARY KEY,
                    source_type TEXT DEFAULT 'documentation',
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    section_name TEXT,
                    section_order INTEGER DEFAULT 1,
                    metadata JSONB,
                    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    chunk_id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES knowledge_documents(document_id) ON DELETE CASCADE,
                    chunk_order INTEGER DEFAULT 1,
                    chunk_title TEXT,
                    chunk_text TEXT NOT NULL,
                    keywords TEXT[],
                    metadata JSONB,
                    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
        _knowledge_tables_checked = True
        return True
    except Exception as e:
        logger.warning(f"Could not auto-create knowledge tables in PostgreSQL: {e}")
        return False


def save_knowledge_document(doc_dict: Dict[str, Any]) -> Optional[int]:
    """Saves a knowledge document into PostgreSQL (or in-memory fallback)."""
    if not is_knowledge_db_available():
        doc_id = len(_in_memory_docs) + 1
        doc_dict["document_id"] = doc_id
        _in_memory_docs.append(doc_dict)
        return doc_id

    try:
        from database.db import get_cursor
        meta_json = psycopg2.extras.Json(doc_dict.get("metadata", {}))
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO knowledge_documents (
                    source_type, source_name, title, content, section_name, section_order, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING document_id;
                """,
                (
                    doc_dict.get("source_type", "documentation"),
                    doc_dict.get("source_name", "docs"),
                    doc_dict.get("title", "Untitled Document"),
                    doc_dict.get("content", ""),
                    doc_dict.get("section_name", "General"),
                    doc_dict.get("section_order", 1),
                    meta_json,
                ),
            )
            row = cur.fetchone()
            if row:
                return row["document_id"] if isinstance(row, dict) else row[0]
    except Exception as e:
        logger.error(f"Failed to save knowledge_document: {e}", exc_info=True)

    return None


def save_knowledge_chunk(chunk_dict: Dict[str, Any]) -> Optional[int]:
    """Saves a knowledge chunk into PostgreSQL (or in-memory fallback)."""
    if not is_knowledge_db_available():
        chunk_id = len(_in_memory_chunks) + 1
        chunk_dict["chunk_id"] = chunk_id
        _in_memory_chunks.append(chunk_dict)
        return chunk_id

    try:
        from database.db import get_cursor
        meta_json = psycopg2.extras.Json(chunk_dict.get("metadata", {}))
        keywords = chunk_dict.get("keywords", [])

        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO knowledge_chunks (
                    document_id, chunk_order, chunk_title, chunk_text, keywords, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING chunk_id;
                """,
                (
                    chunk_dict.get("document_id"),
                    chunk_dict.get("chunk_order", 1),
                    chunk_dict.get("chunk_title", "Chunk"),
                    chunk_dict.get("chunk_text", ""),
                    keywords,
                    meta_json,
                ),
            )
            row = cur.fetchone()
            if row:
                return row["chunk_id"] if isinstance(row, dict) else row[0]
    except Exception as e:
        logger.error(f"Failed to save knowledge_chunk: {e}", exc_info=True)

    return None


def search_knowledge_chunks(query: str, source_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Searches knowledge chunks using keyword and text matching."""
    query_clean = str(query or "").strip().lower()
    if not query_clean:
        return []

    if not is_knowledge_db_available():
        # In-Memory Search Fallback
        results = []
        for c in _in_memory_chunks:
            text = (c.get("chunk_text") or "").lower()
            title = (c.get("chunk_title") or "").lower()
            if query_clean in text or query_clean in title:
                results.append(c)
                if len(results) >= limit:
                    break
        return results

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            pattern = f"%{query_clean}%"
            if source_type:
                cur.execute(
                    """
                    SELECT c.*, d.source_name, d.source_type, d.section_name, d.title as doc_title
                    FROM knowledge_chunks c
                    JOIN knowledge_documents d ON c.document_id = d.document_id
                    WHERE d.source_type = %s AND (LOWER(c.chunk_text) LIKE %s OR LOWER(c.chunk_title) LIKE %s)
                    ORDER BY c.chunk_id ASC LIMIT %s;
                    """,
                    (source_type, pattern, pattern, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT c.*, d.source_name, d.source_type, d.section_name, d.title as doc_title
                    FROM knowledge_chunks c
                    JOIN knowledge_documents d ON c.document_id = d.document_id
                    WHERE LOWER(c.chunk_text) LIKE %s OR LOWER(c.chunk_title) LIKE %s
                    ORDER BY c.chunk_id ASC LIMIT %s;
                    """,
                    (pattern, pattern, limit),
                )
            rows = cur.fetchall()
            if rows:
                return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"Knowledge chunk search failed: {e}")

    return []


def clear_knowledge_index(source_type: Optional[str] = None) -> bool:
    """Clears indexed documents and chunks."""
    global _in_memory_docs, _in_memory_chunks
    _in_memory_docs.clear()
    _in_memory_chunks.clear()

    if not is_knowledge_db_available():
        return True

    try:
        from database.db import get_cursor
        with get_cursor(commit=True) as cur:
            if source_type:
                cur.execute("DELETE FROM knowledge_documents WHERE source_type = %s;", (source_type,))
            else:
                cur.execute("TRUNCATE TABLE knowledge_documents RESTART IDENTITY CASCADE;")
        return True
    except Exception as e:
        logger.error(f"Failed to clear knowledge index: {e}")
        return False


def get_knowledge_index_stats() -> Dict[str, Any]:
    """Returns total indexed documents, total chunks, and last indexed date."""
    if not is_knowledge_db_available():
        return {
            "storage_backend": "in_memory",
            "document_count": len(_in_memory_docs),
            "chunk_count": len(_in_memory_chunks),
            "last_indexed": "In-Memory Session Only",
        }

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) FROM knowledge_documents;")
            doc_cnt = cur.fetchone()
            d_cnt = doc_cnt["count"] if isinstance(doc_cnt, dict) else (doc_cnt[0] if doc_cnt else 0)

            cur.execute("SELECT COUNT(*) FROM knowledge_chunks;")
            chk_cnt = cur.fetchone()
            c_cnt = chk_cnt["count"] if isinstance(chk_cnt, dict) else (chk_cnt[0] if chk_cnt else 0)

            cur.execute("SELECT MAX(indexed_at) FROM knowledge_documents;")
            last_row = cur.fetchone()
            last_date = str(last_row["max"] if isinstance(last_row, dict) else (last_row[0] if last_row else "Never"))

            return {
                "storage_backend": "postgres",
                "document_count": d_cnt,
                "chunk_count": c_cnt,
                "last_indexed": last_date if last_date != "None" else "Never",
            }
    except Exception as e:
        logger.debug(f"Failed to fetch knowledge index stats: {e}")

    return {
        "storage_backend": "error_fallback",
        "document_count": len(_in_memory_docs),
        "chunk_count": len(_in_memory_chunks),
        "last_indexed": "Unknown",
    }
