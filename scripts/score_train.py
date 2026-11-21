"""
scripts/score_train.py

Runs the pipeline on a sample of train cases, compares against train_labels.csv,
and reports accuracy broken down by requirement and by verdict type.

Usage:
    python -m scripts.score_train                    # 50 random train cases
    python -m scripts.score_train --n 100            # 100 cases
    python -m scripts.score_train --cases c0001 c0002  # specific cases
    python -m scripts.score_train --resume           # skip already-done cases
"""
import argparse
import csv
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

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

# import metric scorer
sys.path.insert(0, str(ROOT / "data"))
import metric as metric_module

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


def run(n: int, specific_cases: list[str] | None, top_k: int, resume: bool) -> None:
    log.info("Loading dataset …")
    dataset = VendorVerdictDataset().load()
    requirements = dataset.get_requirements()

    # Load gold labels
    labels_df = dataset.train_labels_df
    gold = {r["id"]: r["verdict"] for r in labels_df.to_dict("records")}

    # Build gold requirement rows grouped by case
    # {case_id: [requirement_id, ...]}
    case_reqs: dict[str, list[str]] = defaultdict(list)
    case_overall_id: dict[str, str] = {}
    for row_id, verdict in gold.items():
        case_id, req_id = row_id.split("__", 1)
        if req_id == "OVERALL":
            case_overall_id[case_id] = row_id
        else:
            case_reqs[case_id].append(req_id)

    # Select cases to evaluate
    all_train_cases = sorted(case_reqs.keys())
    if specific_cases:
        selected = specific_cases
    else:
        random.seed(42)
        selected = random.sample(all_train_cases, min(n, len(all_train_cases)))
        selected = sorted(selected)

    log.info("Evaluating %d train cases …", len(selected))

    # Checkpoint
    checkpoint = ROOT / "train_score.checkpoint.csv"
    results: dict[str, str] = {}
    if resume and checkpoint.exists():
        with open(checkpoint, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                results[r["id"]] = r["verdict"]
        log.info("Resumed — %d rows already done", len(results))

    log.info("Building services …")
    svc = build_services(dataset)

    for idx, case_id in enumerate(selected, 1):
        req_ids = case_reqs.get(case_id, [])
        overall_row_id = case_overall_id.get(case_id)

        req_row_ids = [f"{case_id}__{r}" for r in req_ids]
        all_done = all(rid in results for rid in req_row_ids) and \
                   (overall_row_id is None or overall_row_id in results)
        if all_done:
            log.info("[%d/%d] %s — cached", idx, len(selected), case_id)
            continue

        log.info("[%d/%d] %s — %d requirements", idx, len(selected), case_id, len(req_ids))
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
            gold_v = gold.get(row_id, "?")
            match = "✓" if verdict == gold_v else "✗"
            log.info("    %s → %s  (gold: %s) %s", req_id, verdict, gold_v, match)

        if overall_row_id and overall_row_id not in results:
            overall_verdict = _compute_overall(verdicts, requirements)
            results[overall_row_id] = overall_verdict
            gold_v = gold.get(overall_row_id, "?")
            match = "✓" if overall_verdict == gold_v else "✗"
            log.info("    OVERALL → %s  (gold: %s) %s", overall_verdict, gold_v, match)

        with open(checkpoint, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "verdict"])
            w.writerows(results.items())

    # -------------------------------------------------------------------
    # Score using metric.py
    # -------------------------------------------------------------------
    # Build solution and submission dataframes for the evaluated rows
    eval_ids = [
        row_id for row_id in results
        if row_id.split("__")[0] in selected
    ]

    solution_rows = [{"id": rid, "verdict": gold[rid]} for rid in eval_ids if rid in gold]
    submission_rows = [{"id": rid, "verdict": results[rid]} for rid in eval_ids if rid in gold]

    solution_df = pd.DataFrame(solution_rows)
    submission_df = pd.DataFrame(submission_rows)

    comps = metric_module.components(solution_df, submission_df)

    print("\n" + "="*55)
    print(f"  SCORE REPORT  ({len(selected)} train cases)")
    print("="*55)
    print(f"  Overall score        : {comps['score']:.5f}")
    print(f"  Macro F1 (reqs)      : {comps['macro_f1']:.5f}  (×0.60)")
    print(f"  Overall accuracy     : {comps['overall_accuracy']:.5f}  (×0.20)")
    print(f"  False confidence     : {comps['false_confidence_rate']:.5f}  (×0.20, lower=better)")
    print("="*55)

    # Per-requirement accuracy
    print("\n  Per-requirement accuracy:")
    print(f"  {'Requirement':<12} {'Correct':>7} {'Total':>6} {'Acc':>6}  {'Errors'}")
    print("  " + "-"*52)

    req_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0, "errors": []})
    for rid in eval_ids:
        if "__OVERALL" in rid:
            continue
        case_id, req_id = rid.split("__", 1)
        pred = results.get(rid, "UNKNOWN")
        g = gold.get(rid)
        if g is None:
            continue
        req_stats[req_id]["total"] += 1
        if pred == g:
            req_stats[req_id]["correct"] += 1
        else:
            req_stats[req_id]["errors"].append(f"{pred}→{g}")

    for req_id in sorted(req_stats):
        s = req_stats[req_id]
        acc = s["correct"] / s["total"] if s["total"] else 0
        err_counts = Counter(req_stats[req_id]["errors"]).most_common(3)
        err_str = "  ".join(f"{k}({v})" for k, v in err_counts)
        print(f"  {req_id:<12} {s['correct']:>7} {s['total']:>6} {acc:>5.0%}  {err_str}")

    # Verdict confusion summary
    print("\n  Verdict confusion (pred→gold, top errors):")
    confusion: Counter = Counter()
    for rid in eval_ids:
        if "__OVERALL" in rid:
            continue
        pred = results.get(rid, "UNKNOWN")
        g = gold.get(rid)
        if g and pred != g:
            confusion[f"{pred}→{g}"] += 1
    for pair, count in confusion.most_common(8):
        print(f"    {pair:<25} {count}")

    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Score pipeline on train cases")
    ap.add_argument("--n", type=int, default=50, help="Number of random train cases")
    ap.add_argument("--cases", nargs="+", help="Specific case IDs to evaluate")
    ap.add_argument("--top_k", type=int, default=8)
    ap.add_argument("--resume", action="store_true", default=True,
                    help="Resume from train_score.checkpoint.csv")
    args = ap.parse_args()
    run(args.n, args.cases, args.top_k, args.resume)


if __name__ == "__main__":
    main()
