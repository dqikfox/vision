"""Collect API keys/tokens from documents and images in a directory.

Usage:
    python hive_tools/collect_api_keys.py --root G:/rag-v1/data --output G:/rag-v1/data/api_key_collection.json
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".ini",
    ".env",
    ".cfg",
    ".conf",
    ".toml",
    ".csv",
    ".ts",
    ".js",
    ".mjs",
    ".cjs",
    ".html",
    ".css",
    ".xml",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}

SKIP_DIR_NAMES = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "runs",
}

MAX_TEXT_FILE_BYTES = 2_000_000
MAX_IMAGE_FILE_BYTES = 8_000_000

KEY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b")),
    ("huggingface", re.compile(r"\bhf_[A-Za-zA-Z0-9]{16,}\b")),
    ("github", re.compile(r"\bgh[pousr]_[A-Za-zA-Z0-9]{20,}\b")),
    ("slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "generic_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|token)\b\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{16,})"
        ),
    ),
]

SKIP_VALUE_PATTERN = re.compile(r"(?i)(example|sample|placeholder|changeme|your_|insert_|dummy|test_key)")


@dataclass
class Finding:
    provider_hint: str
    key: str
    source: str
    line: int | None
    method: str


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            if any(part.casefold() in SKIP_DIR_NAMES for part in p.parts):
                continue
            yield p


def _read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_FILE_BYTES:
            return ""
    except Exception:
        return ""

    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


def _read_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            data = zf.read("word/document.xml")
    except Exception:
        return ""
    text = data.decode("utf-8", errors="ignore")
    return re.sub(r"<[^>]+>", " ", text)


def _line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _extract_from_text(text: str, source: str, method: str) -> list[Finding]:
    findings: list[Finding] = []
    if not text:
        return findings

    for provider_hint, pattern in KEY_PATTERNS:
        for match in pattern.finditer(text):
            if provider_hint == "generic_assignment":
                value = match.group(2)
            else:
                value = match.group(0)

            if len(value) < 16 or SKIP_VALUE_PATTERN.search(value):
                continue

            if value.lower().startswith(("http://", "https://")):
                continue

            findings.append(
                Finding(
                    provider_hint=provider_hint,
                    key=value,
                    source=source,
                    line=_line_number_for_offset(text, match.start()),
                    method=method,
                )
            )
    return findings


def _extract_from_image(path: Path) -> list[Finding]:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return []

    try:
        with Image.open(path) as img:
            try:
                if path.stat().st_size > MAX_IMAGE_FILE_BYTES:
                    return []
            except Exception:
                return []
            text = pytesseract.image_to_string(img)
    except Exception:
        return []

    return _extract_from_text(text, str(path), "ocr")


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str]] = set()
    unique: list[Finding] = []
    for item in findings:
        key = (item.key, item.source)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _mask(key: str) -> str:
    if len(key) <= 10:
        return "*" * len(key)
    return f"{key[:6]}...{key[-4:]}"


def _prioritize_images(images: list[Path]) -> list[Path]:
    """Prioritize likely key-containing image filenames first."""
    hot_words = ("key", "token", "secret", "auth", "api", "credential")

    def score(path: Path) -> tuple[int, int]:
        name = path.name.casefold()
        hot = 0 if any(word in name for word in hot_words) else 1
        return (hot, len(name))

    return sorted(images, key=score)


def collect(root: Path, ocr_max_images: int) -> dict[str, object]:
    findings: list[Finding] = []
    scanned_files = 0
    scanned_images = 0

    image_paths: list[Path] = []

    for path in _iter_files(root):
        suffix = path.suffix.lower()

        if suffix in TEXT_EXTENSIONS:
            scanned_files += 1
            text = _read_text(path)
            findings.extend(_extract_from_text(text, str(path), "text"))
        elif suffix == ".docx":
            scanned_files += 1
            text = _read_docx_text(path)
            findings.extend(_extract_from_text(text, str(path), "docx"))
        elif suffix in IMAGE_EXTENSIONS:
            image_paths.append(path)

    prioritized = _prioritize_images(image_paths)
    if ocr_max_images > 0:
        prioritized = prioritized[:ocr_max_images]

    for path in prioritized:
        scanned_images += 1
        findings.extend(_extract_from_image(path))

    unique = _dedupe(findings)

    return {
        "root": str(root),
        "summary": {
            "scanned_text_docs": scanned_files,
            "scanned_images": scanned_images,
            "findings": len(unique),
        },
        "findings": [
            {
                "provider_hint": f.provider_hint,
                "key": f.key,
                "key_masked": _mask(f.key),
                "source": f.source,
                "line": f.line,
                "method": f.method,
            }
            for f in unique
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect API keys from docs/images")
    parser.add_argument("--root", required=True, help="Directory to scan")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--ocr-max-images",
        type=int,
        default=120,
        help="Maximum number of images to OCR (0 = unlimited)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    output = Path(args.output)

    if not root.exists():
        raise FileNotFoundError(f"Root path not found: {root}")

    data = collect(root, ocr_max_images=max(0, int(args.ocr_max_images)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(data["summary"], indent=2))
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
