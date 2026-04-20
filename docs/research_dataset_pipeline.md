# Research Dataset Pipeline (HF Bucket + Local Data)

This pipeline builds a governed JSONL corpus for controlled LLM training and evaluation.

Data sources supported:
- Hugging Face repo/bucket, e.g. `havikz/bucket`
- Local directory, e.g. `G:/rag-v1/data`

The script is intentionally mode-driven:
- `aligned` mode: stricter inclusion
- `research_eval` mode: broader inclusion for controlled analysis

Both modes keep a non-disableable safeguard that excludes actionable harm content from curated output.

## File Locations

- Script: `hive_tools/research_dataset_pipeline.py`
- Mode configs:
  - `configs/llm_data_modes/aligned.json`
  - `configs/llm_data_modes/research_eval.json`

## Install

```powershell
pip install -r requirements.txt
```

## Run (Aligned)

```powershell
python hive_tools/research_dataset_pipeline.py `
  --hf-repo havikz/bucket `
  --hf-repo-type auto `
  --local-root G:/rag-v1/data `
  --mode-config configs/llm_data_modes/aligned.json `
  --output-dir data/curated
```

## Run (Research Eval)

```powershell
python hive_tools/research_dataset_pipeline.py `
  --hf-repo havikz/bucket `
  --hf-repo-type auto `
  --local-root G:/rag-v1/data `
  --mode-config configs/llm_data_modes/research_eval.json `
  --output-dir data/curated
```

## Outputs

For each mode, the script writes:
- `data/curated/curated_<mode>.jsonl`
- `data/curated/summary_<mode>.json`
- `data/curated/hf_snapshot/` (downloaded HF snapshot)

## Notes

- If your repo is private, pass `--hf-token <token>`.
- Use `--clean-cache` to force a fresh HF snapshot.
- Add `--allow-local-only` to proceed with `G:/rag-v1/data` even if HF repo lookup fails.
- Curated records include metadata fields: `risk_level`, `allowed_for_training`, `disallow_actionable_harm`, `content_hash`, and `mode`.
