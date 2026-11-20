from fastapi import APIRouter, HTTPException, Query

from src.services.fact_extraction_service import FactExtractionService

router = APIRouter(
    prefix="/extraction",
    tags=["Fact Extraction"]
)

_extraction_service: FactExtractionService | None = None


def set_extraction_service(service: FactExtractionService):
    global _extraction_service
    _extraction_service = service


def get_extraction_service() -> FactExtractionService:
    if _extraction_service is None:
        raise RuntimeError("Extraction service has not been set.")
    return _extraction_service


@router.post("/{case_id}/{requirement_id}")
def extract_fact(
    case_id: str,
    requirement_id: str,
    top_k: int = Query(8, ge=1, le=20)
):
    try:
        service = get_extraction_service()
        result = service.extract_fact_for_requirement(
            case_id=case_id,
            requirement_id=requirement_id,
            top_k=top_k
        )
        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc