from fastapi import APIRouter, HTTPException, Query

from src.services.retrieval_service import RetrievalService

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"]
)

_retrieval_service: RetrievalService | None = None

def set_retrieval_service(service: RetrievalService):
    global _retrieval_service
    _retrieval_service = service


def get_retrieval_service() -> RetrievalService:
    if _retrieval_service is None:
        raise RuntimeError("Retrieval service not set")
    return _retrieval_service


@router.get("/{case_id}/{requirement_id}")
def retrieve_requirement(case_id: str, requirement_id: str, top_k: int = Query(8, ge=1,le=20)):
    try:
        return (
            get_retrieval_service().retrieve_for_requirement(
                case_id=case_id,
                requirment_id=requirement_id,
                top_k=top_k
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc