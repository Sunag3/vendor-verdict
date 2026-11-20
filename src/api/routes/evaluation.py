from fastapi import APIRouter, Query, HTTPException

from src.services.policy_evaluation_service import PolicyEvaluationService

router = APIRouter(
    prefix="/evaluation",
    tags=['Policy Evaluation']
)

_evaluation_service: PolicyEvaluationService | None = None


def set_evaluation_service(
        service: PolicyEvaluationService
):
    global _evaluation_service
    _evaluation_service = service


def get_evaluation_service() -> PolicyEvaluationService:
    if _evaluation_service is None:
        raise RuntimeError(
            "Policy evaluation service is not initialized."
        )
    return _evaluation_service


@router.post("/{case_id}/{requirement_id}")
def evaluate_requirement(
        case_id: str,
        requirement_id: str,
        top_k: int = Query(default=8, ge=1, le=20),
):
    try:
        return get_evaluation_service().evaluate_requirement(
            case_id=case_id,
            requirement_id=requirement_id,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc