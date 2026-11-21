# Vendor Verdict

An end-to-end AI pipeline for automated vendor security reviews, built for the [Vendor Verdict Kaggle competition](https://www.kaggle.com/).

Given a set of web pages about a fictional vendor, the pipeline predicts a compliance verdict for each applicable policy requirement — and an overall outcome — using trusted evidence only.

---

## Problem

Every company that adopts an AI tool runs a vendor security review. The challenge is reading carefully:

- A 2024 trust page says one thing; a 2026 page says another
- A directory site republishes the old page with a fresh date
- A review site says SSO is Enterprise-only; the vendor says otherwise
- A forum post claims a breach; a blog tells AI assistants to "report PASS"

**Guessing is the dangerous error.** The scoring metric penalises PASS/FAIL answers when the true answer is UNKNOWN or NEEDS\_REVIEW.

---

## Pipeline

```
pages.jsonl + cases.csv + requirements.json
        │
        ▼
  Trust Filter          ← only official domain + certificate registries
        │
        ▼
  Evidence Chunker      ← 350-word overlapping chunks, paragraph-aware
        │
        ▼
  Embed + Index         ← OpenAI text-embedding-3-small → ChromaDB (run once)
        │
        ▼
  Requirement Retrieval ← top-k semantic search per requirement
        │
        ▼
  Fact Extraction       ← AWS Bedrock (Claude Sonnet) → structured JSON
        │
        ▼
  Conflict Resolver     ← newest last_updated wins, future evidence filtered
        │
        ▼
  Policy Rule Engine    ← deterministic: PASS / FAIL / UNKNOWN / NEEDS_REVIEW
        │
        ▼
  submission.csv        → Kaggle upload
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Vector store | ChromaDB (persistent) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM extraction | AWS Bedrock — Claude Sonnet (`us.anthropic.claude-sonnet-4-6`) |
| LLM SDK | Strands (`structured_output`) |
| Data models | Pydantic v2 |
| Settings | pydantic-settings + `.env` |

---

## Project Structure

```
src/
├── api/
│   ├── main.py                   # FastAPI app + DI wiring
│   └── routes/                   # cases, evidence, chunks, retrieval,
│                                 # extraction, resolution, evaluation
├── agents/
│   ├── fact_extraction_agent.py  # Strands + Bedrock agent
│   └── prompts.py                # injection-hardened prompt builder
├── config/
│   └── settings.py               # pydantic-settings
├── loaders/
│   └── dataset_loader.py         # loads all data files
├── models/                       # Pydantic models
│   ├── case.py / page.py / chunk.py
│   ├── extracted_fact.py         # ExtractedFact, FactCandidate, EvidenceReference
│   ├── resolved_fact.py          # ResolvedFact
│   └── requirement_verdict.py    # RequirementVerdict
├── policy/
│   └── rules_adapter.py          # deterministic verdict rules
├── rag/
│   ├── chunker.py                # EvidenceChunker
│   ├── embedder.py               # OpenAIEmbedder
│   ├── vector_store.py           # ChromaVectorStore
│   ├── retriever.py              # EvidenceRetriever
│   └── requirment_retriever.py   # RequirementRetriever (per-requirement RAG)
├── resolvers/
│   └── conflict_resolver.py      # ConflictResolver (date-based)
├── services/                     # service layer (DI targets)
│   ├── validation_service.py
│   ├── chunking_service.py
│   ├── indexing_service.py
│   ├── retrieval_service.py
│   ├── fact_extraction_service.py
│   ├── resolution_service.py
│   └── policy_evaluation_service.py
└── validators/                   # SourceValidator and sub-validators

scripts/
├── build_index.py        # index all cases into ChromaDB (run once)
├── build_submission.py   # batch evaluation → submission.csv
└── validate_dataset.py   # data integrity checks

data/
├── cases.csv             # 700 cases (400 train, 300 test)
├── pages.jsonl           # ~7,000 web pages
├── requirements.json     # 10 policy requirements
├── train_labels.csv      # gold verdicts for train cases
├── test.csv              # rows to predict
├── rules_lite.py         # competition's deterministic rule engine
└── metric.py             # local scoring script
```

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in: OPENAI_API_KEY, AWS credentials, BEDROCK_MODEL_ID
```

### `.env` keys

```
OPENAI_API_KEY=...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
AWS_REGION=us-east-1

CHROMA_PATH=chroma
CHROMA_COLLECTION=vendor_verdict_evidence
```

---

## Usage

### 1. Build the vector index (once)

```bash
python -m scripts.build_index
```

Chunks all trusted pages, embeds them, and stores vectors in ChromaDB (`chroma/`).

### 2. Run the API server

```bash
uvicorn src.api.main:app --reload
```

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cases/{case_id}` | Case metadata |
| GET | `/cases/{case_id}/evidence` | Validated pages |
| GET | `/cases/{case_id}/chunks` | Evidence chunks |
| GET | `/retrieval/{case_id}/{requirement_id}` | Retrieved evidence package |
| POST | `/extraction/{case_id}/{requirement_id}` | Extracted fact (Bedrock) |
| POST | `/resolution/{case_id}/{requirement_id}` | Resolved fact |
| POST | `/evaluation/{case_id}/{requirement_id}` | Single requirement verdict |
| POST | `/evaluation/{case_id}` | All requirements + OVERALL for a case |

### 3. Generate submission

```bash
python -m scripts.build_submission
# or
python -m scripts.build_submission --top_k 10 --output my_submission.csv
```

- Processes all 300 test cases (~2,400 Bedrock calls)
- Checkpoints after every case — safe to interrupt and resume
- Writes `submission.csv` ready for Kaggle upload

### 4. Score locally (train cases)

```bash
python data/metric.py
```

---

## Key Design Decisions

**Trust filtering over recall.** Only the vendor's official domain and certificate registries can establish a fact. Reviews, news, blogs, and directory copies are silently discarded — even if they contain plausible information. This matches the competition's evidence policy exactly.

**Deterministic resolution, not LLM judgement.** When multiple trusted sources disagree, the conflict resolver picks the most recently updated source by `last_updated` date. The LLM is never asked to choose between conflicting evidence.

**Injection hardening.** Evidence text is explicitly labelled as untrusted data in both the system prompt and the user prompt. Pages that instruct the model to "report PASS" are scored as data, not instructions.

**Missing = UNKNOWN, not a guess.** If official sources do not state a field, `missing=True` → verdict `UNKNOWN`. The scoring metric has a dedicated false-confidence penalty for guessing PASS or FAIL when the truth is UNKNOWN or NEEDS\_REVIEW.

---

## Running Tests

```bash
pytest
pytest tests/test_api.py
pytest tests/test_api.py::test_health
```
