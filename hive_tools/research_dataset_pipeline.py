"""Build a governed research dataset from Hugging Face buckets and local folders.

This script supports two runtime modes via JSON config:
- aligned: stricter filtering and redaction for safer default experimentation
- research_eval: broader inclusion for controlled security research and evaluation

Both modes keep non-disableable safeguards that block actionable harm content.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download, sync_bucket
from huggingface_hub.errors import RepositoryNotFoundError

DEFAULT_EXTENSIONS = {".txt", ".md", ".json", ".jsonl", ".csv", ".log"}

# Non-disableable safeguard patterns: always excluded from training output.
ACTIONABLE_HARM_PATTERNS = [
    r"\bbuild\s+malware\b",
    r"\bbypass\s+authentication\b",
    r"\bexploit\s+chain\b",
    r"\bweaponize\b",
    r"\bphishing\s+kit\b",
]


@dataclass
class ModeConfig:
    """Mode-specific controls for data curation."""

    name: str
    include_sensitive: bool
    max_chars_per_record: int
    min_chars_per_record: int
    redact_emails: bool
    redact_ips: bool
    allow_patterns: list[str]
    ignore_patterns: list[str]


def _load_mode_config(path: Path) -> ModeConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ModeConfig(
        name=raw["mode"],
        include_sensitive=bool(raw.get("include_sensitive", False)),
        max_chars_per_record=int(raw.get("max_chars_per_record", 12000)),
        min_chars_per_record=int(raw.get("min_chars_per_record", 60)),
        redact_emails=bool(raw.get("redact_emails", True)),
        redact_ips=bool(raw.get("redact_ips", True)),
        allow_patterns=list(raw.get("allow_patterns", ["**/*"])),
        ignore_patterns=list(raw.get("ignore_patterns", [])),
    )


def _is_text_file(path: Path, extensions: set[str]) -> bool:
    return path.suffix.lower() in extensions


def _iter_text_files(root: Path, extensions: set[str]) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and _is_text_file(path, extensions):
            yield path


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
    except Exception:
        return None


def _redact(text: str, cfg: ModeConfig) -> str:
    cleaned = text
    if cfg.redact_emails:
        cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", cleaned)
    if cfg.redact_ips:
        cleaned = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]", cleaned)
    return cleaned


def _contains_actionable_harm(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in ACTIONABLE_HARM_PATTERNS)


def _risk_level(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["exploit", "payload", "credential", "malware", "phishing", "ransomware"]):
        return "high"
    if any(word in lowered for word in ["vulnerability", "red team", "adversarial", "security", "forensic"]):
        return "medium"
    return "low"


def _clip(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars]


def _make_record(text: str, source_path: str, cfg: ModeConfig) -> dict[str, Any] | None:
    text = _redact(text, cfg)
    text = _clip(text, cfg.max_chars_per_record).strip()

    if len(text) < cfg.min_chars_per_record:
        return None

    # Non-disableable policy gate.
    if _contains_actionable_harm(text):
        return None

    risk = _risk_level(text)
    if not cfg.include_sensitive and risk == "high":
        return None

    content_hash = sha256(text.encode("utf-8")).hexdigest()
    return {
        "text": text,
        "source": source_path,
        "risk_level": risk,
        "allowed_for_training": True,
        "disallow_actionable_harm": True,
        "content_hash": content_hash,
        "mode": cfg.name,
    }


def _download_hf_snapshot(
    repo_id: str,
    repo_type: str,
    target_dir: Path,
    allow_patterns: list[str],
    ignore_patterns: list[str],
    token: str | None,
) -> Path:
    snapshot_path = snapshot_download(
        repo_id=repo_id,
        repo_type=repo_type,
        local_dir=target_dir,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
        token=token,
    )
    return Path(snapshot_path)


def _normalize_bucket_id(bucket_id: str) -> str:
    if bucket_id.startswith("hf://buckets/"):
        return bucket_id.removeprefix("hf://buckets/").strip("/")
    return bucket_id.strip("/")


def _download_hf_bucket(
    bucket_id: str,
    target_dir: Path,
    allow_patterns: list[str],
    ignore_patterns: list[str],
    token: str | None,
) -> Path:
    normalized = _normalize_bucket_id(bucket_id)
    source = f"hf://buckets/{normalized}"
    sync_bucket(
        source=source,
        dest=str(target_dir),
        include=allow_patterns or None,
        exclude=ignore_patterns or None,
        token=token,
        quiet=True,
    )
    return target_dir


def _download_hf_snapshot_with_fallback(
    repo_id: str,
    repo_type: str,
    target_dir: Path,
    allow_patterns: list[str],
    ignore_patterns: list[str],
    token: str | None,
) -> Path:
    """Download HF snapshot and auto-detect repo type when requested."""
    if repo_type == "bucket":
        return _download_hf_bucket(repo_id, target_dir, allow_patterns, ignore_patterns, token)

    if repo_type != "auto":
        return _download_hf_snapshot(repo_id, repo_type, target_dir, allow_patterns, ignore_patterns, token)

    errors: list[str] = []
    try:
        return _download_hf_bucket(repo_id, target_dir, allow_patterns, ignore_patterns, token)
    except Exception as exc:
        errors.append(f"bucket: {exc}")

    for candidate in ["dataset", "model", "space"]:
        try:
            return _download_hf_snapshot(repo_id, candidate, target_dir, allow_patterns, ignore_patterns, token)
        except RepositoryNotFoundError as exc:
            errors.append(f"{candidate}: {exc}")
            continue
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
            continue

    raise RuntimeError(
        f"HF source could not be resolved as bucket/dataset/model/space. Repo: {repo_id}. Errors: {' | '.join(errors)}"
    )


def _collect_records(roots: Iterable[Path], cfg: ModeConfig, extensions: set[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for root in roots:
        for file_path in _iter_text_files(root, extensions):
            payload = _read_text(file_path)
            if not payload:
                continue
            rec = _make_record(payload, str(file_path), cfg)
            if not rec:
                continue
            digest = rec["content_hash"]
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            records.append(rec)
    return records


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Curate governed corpus from HF bucket + local data")
    parser.add_argument("--hf-repo", required=True, help="Hugging Face repo id, e.g. havikz/bucket")
    parser.add_argument(
        "--hf-repo-type",
        default="auto",
        choices=["auto", "bucket", "dataset", "model", "space"],
        help="Hugging Face source type",
    )
    parser.add_argument("--local-root", required=True, help="Local folder path, e.g. G:/rag-v1/data")
    parser.add_argument("--mode-config", required=True, help="Path to mode config JSON")
    parser.add_argument("--output-dir", default="data/curated", help="Output directory")
    parser.add_argument("--hf-token", default=None, help="HF token (or set HF_TOKEN env var)")
    parser.add_argument("--clean-cache", action="store_true", help="Delete previous HF cache before fetching")
    parser.add_argument(
        "--allow-local-only",
        action="store_true",
        help="If HF fetch fails, continue curation using only --local-root",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = _load_mode_config(Path(args.mode_config))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hf_cache_dir = output_dir / "hf_snapshot"
    if args.clean_cache and hf_cache_dir.exists():
        shutil.rmtree(hf_cache_dir)
    hf_cache_dir.mkdir(parents=True, exist_ok=True)

    token = args.hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    token_source = "cli" if args.hf_token else "env" if token else "none"

    local_root = Path(args.local_root)
    if not local_root.exists():
        raise FileNotFoundError(f"Local root not found: {local_root}")

    roots: list[Path] = [local_root]
    hf_status = "not_attempted"
    hf_root: Path | None = None
    try:
        hf_root = _download_hf_snapshot_with_fallback(
            repo_id=args.hf_repo,
            repo_type=args.hf_repo_type,
            target_dir=hf_cache_dir,
            allow_patterns=cfg.allow_patterns,
            ignore_patterns=cfg.ignore_patterns,
            token=token,
        )
        roots.insert(0, hf_root)
        hf_status = "ok"
    except Exception as exc:
        hf_status = f"failed: {exc}"
        if not args.allow_local_only:
            raise

    records = _collect_records(roots, cfg, DEFAULT_EXTENSIONS)
    out_jsonl = output_dir / f"curated_{cfg.name}.jsonl"
    total = _write_jsonl(out_jsonl, records)

    summary = {
        "mode": cfg.name,
        "records": total,
        "hf_repo": args.hf_repo,
        "hf_repo_type": args.hf_repo_type,
        "hf_snapshot": str(hf_root) if hf_root else None,
        "hf_status": hf_status,
        "hf_token_source": token_source,
        "local_root": str(local_root),
        "output": str(out_jsonl),
    }
    (output_dir / f"summary_{cfg.name}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
