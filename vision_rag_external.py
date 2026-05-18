"""Vision RAG - External Knowledge Integration

Indexes external knowledge sources into Vision's RAG system:
1. C:\project\skills - Shared skills repository
2. C:\Users\CHANN0$\Documents\unsloth_data - ULTRON corpus
3. I:\My Drive\Z\X\rag-v1-package - Production RAG package

Usage:
    python vision_rag_external.py --index-all
    python vision_rag_external.py --index skills
    python vision_rag_external.py --search "agent coordination patterns"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from vision_rag import RAGIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# External knowledge source paths
SKILLS_REPO = Path(os.environ.get("SKILLS_REPO_PATH", r"C:\project\skills"))
ULTRON_CORPUS = Path(os.environ.get("ULTRON_CORPUS_PATH", r"C:\Users\CHANN0$\Documents\unsloth_data"))
RAG_PACKAGE = Path(os.environ.get("RAG_PACKAGE_PATH", r"I:\My Drive\Z\X\rag-v1-package"))

# Vision RAG database
VISION_RAG_DB = Path("vision_external_knowledge.db")


def index_skills_repo(rag_index: RAGIndex) -> int:
    """Index C:\project\skills repository.

    Args:
        rag_index: Vision RAG index instance

    Returns:
        Number of files indexed
    """
    if not SKILLS_REPO.exists():
        logger.warning(f"Skills repo not found: {SKILLS_REPO}")
        return 0

    logger.info(f"Indexing skills repository: {SKILLS_REPO}")

    # Index all skill directories
    count = 0
    for skill_dir in SKILLS_REPO.iterdir():
        if not skill_dir.is_dir():
            continue

        # Look for SKILL.md, README.md, or .md files
        for md_file in skill_dir.glob("**/*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rag_index.add_document(
                    path=str(md_file.relative_to(SKILLS_REPO)),
                    content=content,
                    metadata={
                        "source": "skills_repo",
                        "skill_name": skill_dir.name,
                        "file_type": ".md"
                    }
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to index {md_file}: {e}")

    logger.info(f"Indexed {count} skill documents")
    return count


def index_ultron_corpus(rag_index: RAGIndex) -> int:
    """Index ULTRON training corpus.

    Args:
        rag_index: Vision RAG index instance

    Returns:
        Number of files indexed
    """
    if not ULTRON_CORPUS.exists():
        logger.warning(f"ULTRON corpus not found: {ULTRON_CORPUS}")
        return 0

    logger.info(f"Indexing ULTRON corpus: {ULTRON_CORPUS}")

    # Index all .txt files
    count = 0
    for txt_file in ULTRON_CORPUS.glob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            rag_index.add_document(
                path=str(txt_file.name),
                content=content,
                metadata={
                    "source": "ultron_corpus",
                    "file_type": ".txt",
                    "category": extract_category_from_filename(txt_file.name)
                }
            )
            count += 1
            logger.info(f"  Indexed: {txt_file.name}")
        except Exception as e:
            logger.warning(f"Failed to index {txt_file}: {e}")

    logger.info(f"Indexed {count} ULTRON corpus documents")
    return count


def index_rag_package(rag_index: RAGIndex) -> int:
    """Index production RAG package documentation.

    Args:
        rag_index: Vision RAG index instance

    Returns:
        Number of files indexed
    """
    if not RAG_PACKAGE.exists():
        logger.warning(f"RAG package not found: {RAG_PACKAGE}")
        return 0

    logger.info(f"Indexing RAG package: {RAG_PACKAGE}")

    # Index README, docs, and Python files
    count = 0
    patterns = ["**/*.md", "**/*.txt", "**/*.py"]

    for pattern in patterns:
        for file in RAG_PACKAGE.glob(pattern):
            # Skip binary directories
            if any(skip in str(file) for skip in ["__pycache__", ".mypy_cache", "vector_db"]):
                continue

            try:
                content = file.read_text(encoding="utf-8")
                rag_index.add_document(
                    path=str(file.relative_to(RAG_PACKAGE)),
                    content=content,
                    metadata={
                        "source": "rag_package",
                        "file_type": file.suffix,
                        "category": file.parent.name
                    }
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to index {file}: {e}")

    logger.info(f"Indexed {count} RAG package documents")
    return count


def extract_category_from_filename(filename: str) -> str:
    """Extract category from ULTRON corpus filename.

    Examples:
        00_dataset_manifest.txt -> dataset_manifest
        04_ultron_persona_and_operating_playbook.txt -> ultron_persona
    """
    # Remove number prefix and extension
    name = filename.split("_", 1)[-1].rsplit(".", 1)[0]
    # Take first part before next underscore
    return name.split("_")[0] if "_" in name else name


def search_external_knowledge(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search across all external knowledge sources.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of search results with source attribution
    """
    if not VISION_RAG_DB.exists():
        logger.error("External knowledge index not found. Run with --index-all first.")
        return []

    rag_index = RAGIndex(str(VISION_RAG_DB))
    results = rag_index.search(query, limit=limit)

    # Add source attribution
    for result in results:
        source = result.get("metadata", {}).get("source", "unknown")
        if source == "skills_repo":
            result["source_path"] = SKILLS_REPO / result["path"]
        elif source == "ultron_corpus":
            result["source_path"] = ULTRON_CORPUS / result["path"]
        elif source == "rag_package":
            result["source_path"] = RAG_PACKAGE / result["path"]

    return results


def print_search_results(results: list[dict[str, Any]]) -> None:
    """Pretty print search results."""
    if not results:
        print("\nNo results found.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(results)} results:")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        source = result.get("metadata", {}).get("source", "unknown")
        path = result["path"]
        score = result.get("score", 0.0)
        content = result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]

        print(f"{i}. [{source}] {path} (score: {score:.3f})")
        print(f"   {content}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vision RAG External Knowledge Integration")
    parser.add_argument("--index-all", action="store_true", help="Index all external knowledge sources")
    parser.add_argument("--index", choices=["skills", "ultron", "rag"], help="Index specific source")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Search result limit")

    args = parser.parse_args()

    if args.index_all or args.index:
        # Initialize RAG index
        rag_index = RAGIndex(str(VISION_RAG_DB))

        total_indexed = 0

        if args.index_all or args.index == "skills":
            total_indexed += index_skills_repo(rag_index)

        if args.index_all or args.index == "ultron":
            total_indexed += index_ultron_corpus(rag_index)

        if args.index_all or args.index == "rag":
            total_indexed += index_rag_package(rag_index)

        logger.info(f"Total documents indexed: {total_indexed}")

    elif args.search:
        results = search_external_knowledge(args.search, limit=args.limit)
        print_search_results(results)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
