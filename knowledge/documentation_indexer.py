"""
OSMOS Agent Knowledge Base — Documentation Indexer (Phase 8.5)
==============================================================
Heading-based markdown document parser and indexer for docs/ files and system rules.

Offline & Read-Only Guarantee:
Indexes markdown files using regex heading splitting and keyword extraction.
Zero LLM or internet dependency. Never mutates customer data.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional

from knowledge.knowledge_repository import (
    save_knowledge_document,
    save_knowledge_chunk,
    clear_knowledge_index,
    get_knowledge_index_stats,
)

logger = logging.getLogger("OSMOS_DOCUMENTATION_INDEXER")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at", "by", "from",
    "for", "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "of", "in", "on", "off", "over", "under", "again",
    "further", "this", "that", "these", "those", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing", "can", "could",
    "should", "would", "must", "will", "shall", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "le", "la", "les", "du", "de", "des", "un", "une", "et", "ou", "en", "dans"
}


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extracts top non-stopword keywords from text for search indexing."""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:top_n]]


def split_markdown_into_sections(markdown_text: str) -> List[Dict[str, Any]]:
    """Splits markdown text by heading markers (#, ##, ###)."""
    sections: List[Dict[str, Any]] = []
    lines = markdown_text.splitlines()

    current_title = "Overview"
    current_lines: List[str] = []
    section_order = 1

    for line in lines:
        match = re.match(r'^(#{1,3})\s+(.+)$', line.strip())
        if match:
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append({
                        "section_name": current_title,
                        "section_order": section_order,
                        "content": content,
                    })
                    section_order += 1
                current_lines = []
            current_title = match.group(2).strip()
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({
                "section_name": current_title,
                "section_order": section_order,
                "content": content,
            })

    return sections


def create_chunks_from_sections(
    sections: List[Dict[str, Any]],
    max_chars: int = 1200,
) -> List[Dict[str, Any]]:
    """Splits section contents into chunks of max ~1200 characters."""
    chunks: List[Dict[str, Any]] = []
    chunk_order = 1

    for sec in sections:
        s_title = sec.get("section_name", "Section")
        s_content = sec.get("content", "")

        if len(s_content) <= max_chars:
            chunks.append({
                "chunk_order": chunk_order,
                "chunk_title": s_title,
                "chunk_text": s_content,
                "keywords": extract_keywords(s_content),
                "metadata": {"section_name": s_title},
            })
            chunk_order += 1
        else:
            # Paragraph or character split
            paragraphs = s_content.split("\n\n")
            current_chunk: List[str] = []
            current_len = 0

            for p in paragraphs:
                if current_len + len(p) > max_chars and current_chunk:
                    text_block = "\n\n".join(current_chunk).strip()
                    chunks.append({
                        "chunk_order": chunk_order,
                        "chunk_title": f"{s_title} (Part {chunk_order})",
                        "chunk_text": text_block,
                        "keywords": extract_keywords(text_block),
                        "metadata": {"section_name": s_title},
                    })
                    chunk_order += 1
                    current_chunk = [p]
                    current_len = len(p)
                else:
                    current_chunk.append(p)
                    current_len += len(p)

            if current_chunk:
                text_block = "\n\n".join(current_chunk).strip()
                chunks.append({
                    "chunk_order": chunk_order,
                    "chunk_title": f"{s_title} (Part {chunk_order})",
                    "chunk_text": text_block,
                    "keywords": extract_keywords(text_block),
                    "metadata": {"section_name": s_title},
                })
                chunk_order += 1

    return chunks


def parse_markdown_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Reads and parses a single markdown document into sections and chunks."""
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None

    try:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        title_match = re.search(r'^#\s+(.+)$', raw_text, re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else filename.replace(".md", "").replace("_", " ").title()

        sections = split_markdown_into_sections(raw_text)
        chunks = create_chunks_from_sections(sections)

        return {
            "source_type": "documentation",
            "source_name": filename,
            "title": doc_title,
            "content": raw_text[:2000],  # Header preview
            "sections": sections,
            "chunks": chunks,
        }
    except Exception as e:
        logger.error(f"Error parsing markdown file {file_path}: {e}")

    return None


def index_system_governance_rules() -> Dict[str, Any]:
    """Indexes core OSMOS governance rules into knowledge memory."""
    rules_text = """
    # OSMOS System Governance Rules
    1. Agents are strictly READ-ONLY and advisory. No automated modification of customer data.
    2. All operational actions require explicit Human-in-the-Loop administrative approval in the Approval Queue.
    3. LLM calls are strictly button-triggered only (advisory executive summaries).
    4. Stable personas are official segment representations; dynamic personas are exploratory.
    5. Campaign simulation generates closed-loop event traces without sending real emails or SMS.
    6. Single-entity Digital Twin optimization must be preserved across all modules.
    7. Database audit errors take precedence over agent recommendations; audit schema before presentation.
    """
    sections = split_markdown_into_sections(rules_text)
    chunks = create_chunks_from_sections(sections)

    doc_id = save_knowledge_document({
        "source_type": "system_rule",
        "source_name": "OSMOS_Governance_Rules",
        "title": "OSMOS System Governance Rules",
        "content": rules_text,
        "section_name": "Governance",
        "section_order": 1,
        "metadata": {"rule_type": "system_governance"},
    })

    if doc_id:
        for chk in chunks:
            chk["document_id"] = doc_id
            save_knowledge_chunk(chk)

    return {"status": "indexed", "document_title": "OSMOS System Governance Rules", "chunks": len(chunks)}


def index_documentation_folder(docs_path: str = "docs/") -> Dict[str, Any]:
    """Indexes all markdown files in the specified documentation folder."""
    if not os.path.exists(docs_path):
        # Fallback to relative docs/ search
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

    if not os.path.exists(docs_path):
        logger.warning(f"Documentation directory '{docs_path}' does not exist.")
        return {"indexed_files": 0, "total_chunks": 0}

    indexed_count = 0
    total_chunks = 0

    # 1. Index system governance rules first
    index_system_governance_rules()

    # 2. Index docs/ folder
    for fname in os.listdir(docs_path):
        if fname.endswith(".md"):
            fpath = os.path.join(docs_path, fname)
            parsed = parse_markdown_file(fpath)
            if parsed:
                doc_id = save_knowledge_document({
                    "source_type": "documentation",
                    "source_name": parsed["source_name"],
                    "title": parsed["title"],
                    "content": parsed["content"],
                    "section_name": "Overview",
                    "section_order": 1,
                    "metadata": {"file_path": fpath},
                })

                if doc_id:
                    for chk in parsed["chunks"]:
                        chk["document_id"] = doc_id
                        save_knowledge_chunk(chk)

                    indexed_count += 1
                    total_chunks += len(parsed["chunks"])

    logger.info(f"Indexed {indexed_count} documentation files with {total_chunks} total chunks.")
    return {"indexed_files": indexed_count, "total_chunks": total_chunks}


def reindex_all_docs(docs_path: str = "docs/") -> Dict[str, Any]:
    """Clears existing index and reindexes all documentation files."""
    clear_knowledge_index()
    res = index_documentation_folder(docs_path=docs_path)
    stats = get_knowledge_index_stats()
    res.update(stats)
    return res
