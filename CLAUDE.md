# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (activate venv first)
pip install -r requirements.txt

# Run the API server
uvicorn src.api.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_api.py

# Run a single test function
pytest tests/test_api.py::test_health
```

## Architecture

This is a **FastAPI evidence-review pipeline** for a vendor evaluation competition. The goal is to determine whether vendor claims are supported by trustworthy evidence from the web.

### Data flow

```
data/ (CSV + JSONL)
  └─► VendorVerdictDataset (loader)
        └─► CaseService / ValidationService / ChunkingService
              └─► FastAPI routes
```

The dataset is loaded once at startup in `src/api/main.py` and injected into each service. Services are registered into their respective route modules via `set_*_service()` module-level functions (a simple DI pattern — no framework).

### Core pipeline

1. **Load** — `VendorVerdictDataset` reads `cases.csv`, `pages.jsonl`, `requirements.json`, and label/test CSVs. `get_case()` assembles a `VendorCase` with its associated `VendorPage` list.

2. **Validate** — `SourceValidator` runs four independent checks on each page:
   - `domain_validator`: URL matches `case.official_domain`
   - `entity_validator`: publisher matches `case.legal_entity`
   - `registry_validator`: source is a known certificate registry
   - `injection_scanner`: regex check for prompt injection patterns

   Trust logic (in priority order): injection → official domain match → registry + entity match → untrusted source types → reject everything else.

3. **Chunk** — `EvidenceChunker` splits validated pages into overlapping chunks (default 350 words, 40-word overlap). Splitting is paragraph-aware: paragraphs are kept together unless they exceed `max_words`, in which case they are split internally. The chunker is in `src/rag/chunker.py`; `text_cleaner.py` normalises unicode and collapses whitespace before splitting.

4. **Serve** — Three route groups: `/cases` (case metadata), `/cases/{id}/evidence` (validation results), `/cases/{id}/chunks` (chunked evidence ready for RAG).

### Key model relationships

- `VendorCase` → has many `VendorPage` (joined at load time by `case_id`)
- `VendorPage` + `SourceValidationResult` → `ValidatedEvidencePage`
- `ValidatedEvidencePage` → chunked into `EvidenceChunk` (only if `usable_evidence=True`)
- `EvidenceChunk` carries the full provenance of its source page and all validation flags

### Known field mismatch

`EvidenceChunk` (in `src/models/chunk.py`) has a field named `last_updated`, but `EvidenceChunker.chunk_page()` (in `src/rag/chunker.py`) passes `last_updated_date=` — copied from `VendorPage.last_updated_date`. These must stay in sync.

### Settings

`src/config/settings.py` uses `pydantic-settings`. All paths are derived from `settings.base_dir` (the `src/` parent). Override via `.env` — see `.env.example` for available keys. `AS_OF_DATE` controls temporal evidence filtering.

### Data files

All live under `data/`:
- `cases.csv` — one row per vendor case (`case_id`, `split`, `vendor`, `legal_entity`, `official_domain`, …)
- `pages.jsonl` — one JSON object per line, each a `VendorPage`
- `requirements.json` — evaluation rubric / criteria
- `train_labels.csv` / `test.csv` / `sample_submission.csv` — competition splits
