"""
scripts/build_submission.py

Runs the full RAG + Bedrock pipeline over all test cases and writes submission.csv.
Checkpoints after each case so the run can be interrupted and resumed.

Usage:
    python -m scripts.build_submission
    python -m scripts.build_submission --top_k 8 --output submission.csv
"""
import argparse
import csv
import logging
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config.settings import settings
from src.loaders.dataset_loader import VendorVerdictDataset
from src.rag.embedder import OpenAIEmbedder
from src.rag.vector_store import ChromaVectorStore
from src.rag.retriever import EvidenceRetriever
from src.services.chunking_service import ChunkingService
from src.services.validation_service import ValidationService
from src.rag.requirment_retriever import RequirementRetriever
from src.services.retrieval_service import RetrievalService
from src.agents.fact_extraction_agent import FactExtractionAgent
from src.services.fact_extraction_service import FactExtractionService
from src.resolvers.conflict_resolver import ConflictResolver
from src.services.resolution_service import ResolutionService
from src.policy.rules_adapter import RulesAdapter
from src.services.policy_evaluation_service import (
    PolicyEvaluationService,
    _compute_overall,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def build_services(dataset: VendorVerdictDataset) -> PolicyEvaluationService:
    validation_service = ValidationService(dataset=dataset)
    chunking_service = ChunkingService(
        dataset=dataset,
        validation_service=validation_service,
    )
    embedder = OpenAIEmbedder()
    vector_store = ChromaVectorStore()
    retriever = EvidenceRetriever(embedder=embedder, vector_store=vector_store)
    requirement_retriever = RequirementRetriever(dataset=dataset, retriever=retriever)
    retrieval_service = RetrievalService(requirement_retriever=requirement_retriever)
    fact_extraction_agent = FactExtractionAgent()
    fact_extraction_service = FactExtractionService(
        retrieval_service=retrieval_service,
        extraction_agent=fact_extraction_agent,
    )
    conflict_resolver = ConflictResolver(as_of_date=settings.as_of_date)
    resolution_service = ResolutionService(
        extraction_service=fact_extraction_service,
        resolver=conflict_resolver,
    )
    rules_adapter = RulesAdapter(as_of_date=settings.as_of_date)
    return PolicyEvaluationService(
        dataset=dataset,
        resolution_service=resolution_service,
        rules_adapter=rules_adapter,
    )


def run(top_k: int, output: Path) -> None:
    log.info("Loading dataset …")
    dataset = VendorVerdictDataset().load()
    requirements = dataset.get_requirements()

    log.info("Building services …")
    svc = build_services(dataset)

    # -------------------------------------------------------------------
    # Read test.csv — group by case
    # -------------------------------------------------------------------
    test_rows = dataset.test_df.to_dict("records")

    # case_id → [requirement_id, ...]  (non-OVERALL rows only)
    case_reqs: dict[str, list[str]] = defaultdict(list)
    # case_id → row_id  for OVERALL rows
    case_overall_id: dict[str, str] = {}

    for row in test_rows:
        cid = row["case_id"]
        rid = row["requirement_id"]
        if rid == "OVERALL":
            case_overall_id[cid] = row["id"]
        else:
            case_reqs[cid].append(rid)

    all_case_ids = sorted(set(case_reqs) | set(case_overall_id))
    log.info("Test cases: %d", len(all_case_ids))

    # -------------------------------------------------------------------
    # Resume from checkpoint if one exists
    # -------------------------------------------------------------------
    checkpoint = output.with_suffix(".checkpoint.csv")
    results: dict[str, str] = {}  # {row_id: verdict}

    if checkpoint.exists():
        with open(checkpoint, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                results[r["id"]] = r["verdict"]
        log.info("Resumed from checkpoint — %d rows already done", len(results))

    # -------------------------------------------------------------------
    # Evaluate each case
    # -------------------------------------------------------------------
    for idx, case_id in enumerate(all_case_ids, 1):
        req_ids = case_reqs.get(case_id, [])
        overall_row_id = case_overall_id.get(case_id)

        # Skip entirely if already complete
        req_row_ids = [f"{case_id}__{r}" for r in req_ids]
        all_done = all(rid in results for rid in req_row_ids) and \
                   (overall_row_id is None or overall_row_id in results)
        if all_done:
            log.info("[%d/%d] %s — cached", idx, len(all_case_ids), case_id)
            continue

        log.info("[%d/%d] %s — %d requirements", idx, len(all_case_ids), case_id, len(req_ids))
        verdicts: dict[str, str] = {}

        for req_id in req_ids:
            row_id = f"{case_id}__{req_id}"
            if row_id in results:
                verdicts[req_id] = results[row_id]
                continue

            try:
                result = svc.evaluate_requirement(
                    case_id=case_id,
                    requirement_id=req_id,
                    top_k=top_k,
                )
                verdict = result.verdict
            except Exception as exc:
                log.warning("  %s/%s ERROR: %s", case_id, req_id, exc)
                verdict = "UNKNOWN"

            verdicts[req_id] = verdict
            results[row_id] = verdict
            log.info("    %s → %s", req_id, verdict)

        # Compute OVERALL from this case's verdicts
        if overall_row_id and overall_row_id not in results:
            overall_verdict = _compute_overall(verdicts, requirements)
            results[overall_row_id] = overall_verdict
            log.info("    OVERALL → %s", overall_verdict)

        # Save checkpoint
        with open(checkpoint, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "verdict"])
            w.writerows(results.items())

    # -------------------------------------------------------------------
    # Write final submission.csv in test.csv row order
    # -------------------------------------------------------------------
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "verdict"])
        for row in test_rows:
            w.writerow([row["id"], results.get(row["id"], "UNKNOWN")])

    log.info("Written: %s  (%d rows)", output, len(test_rows))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Kaggle submission CSV")
    ap.add_argument("--top_k", type=int, default=8, help="Evidence chunks per requirement")
    ap.add_argument("--output", type=Path, default=ROOT / "submission.csv")
    args = ap.parse_args()
    run(args.top_k, args.output)


if __name__ == "__main__":
    main()
