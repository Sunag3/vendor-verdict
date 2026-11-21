import logging

from src.loaders.dataset_loader import VendorVerdictDataset

from src.models.requirement_verdict import RequirementVerdict

from src.policy.rules_adapter import RulesAdapter

from src.services.resolution_service import ResolutionService

log = logging.getLogger(__name__)


def _req_applies(req: dict, tier: str | None, users: int | None) -> bool:
    aw = req.get("applies_when", {})
    if tier and tier in aw.get("tiers", []):
        return True
    min_users = aw.get("or_min_users")
    return min_users is not None and users is not None and users >= min_users


def _compute_overall(verdicts: dict[str, str], requirements: list[dict]) -> str:
    sev = {r["id"]: r["severity"] for r in requirements}
    if any(v == "FAIL" and sev.get(k) == "blocker" for k, v in verdicts.items()):
        return "BLOCKED"
    if any(v == "FAIL" and sev.get(k) == "major" for k, v in verdicts.items()) or \
       any(v in ("UNKNOWN", "NEEDS_REVIEW") for v in verdicts.values()):
        return "CONDITIONAL"
    return "READY_FOR_APPROVAL"


class PolicyEvaluationService:

    def __init__(self,
                dataset: VendorVerdictDataset,
                resolution_service: ResolutionService,
                rules_adapter: RulesAdapter
                
                ):
        self.dataset = dataset
        self.rules_adapter = rules_adapter
        self.resolution_service = resolution_service


    def evaluate_requirement(
            self,
            case_id: str,
            requirement_id: str,
            top_k: int = 8,
    ) -> RequirementVerdict:

        requirement = (
            self.dataset.get_requirement(requirement_id)
        )

        resolved = (
            self.resolution_service.resolve_requirement(
                case_id=case_id,
                requirement_id=requirement_id,
                top_k=top_k,
            )
        )

        verdict, reason = (
            self.rules_adapter.evaluate(
                requirement=requirement,
                resolved=resolved,
            )
        )

        return RequirementVerdict(
            case_id=case_id,
            requirement_id=requirement_id,
            requirement_title=requirement['title'],
            field_name=requirement['field'],
            severity=requirement['severity'],
            verdict=verdict,
            resolved_value=resolved.value,
            resolved_records=resolved.records,
            evidence=resolved.evidence,
            reason=reason,
            resolution_status=resolved.resolution_status,
            conflict=resolved.conflict,
        )

    def evaluate_case(
            self,
            case_id: str,
            top_k: int = 8,
    ) -> dict:
        case = self.dataset.get_case(case_id)
        requirements = self.dataset.get_requirements()

        applicable = [
            req for req in requirements
            if _req_applies(req, case.tier, case.users)
        ]

        verdicts: dict[str, str] = {}
        details: list[dict] = []

        for req in applicable:
            req_id = req["id"]
            try:
                result = self.evaluate_requirement(
                    case_id=case_id,
                    requirement_id=req_id,
                    top_k=top_k,
                )
                verdicts[req_id] = result.verdict
                details.append(result.model_dump())
            except Exception as exc:
                log.warning("evaluate_case %s/%s error: %s", case_id, req_id, exc)
                verdicts[req_id] = "UNKNOWN"
                details.append({
                    "case_id": case_id,
                    "requirement_id": req_id,
                    "verdict": "UNKNOWN",
                    "reason": str(exc),
                })

        overall = _compute_overall(verdicts, requirements)

        return {
            "case_id": case_id,
            "overall": overall,
            "verdicts": verdicts,
            "details": details,
        }