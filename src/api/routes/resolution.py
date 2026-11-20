from fastapi import APIRouter, HTTPException, Query

from src.services.resolution_service import ResolutionService


router = APIRouter(
    prefix="/resolution",
    tags=["Resolution"],
)


_resolution_service: ResolutionService | None = None

def set_resolution_service(service: ResolutionService) -> None:
    global _resolution_service
    _resolution_service = service


def get_resolution_service() -> ResolutionService:
    if _resolution_service is None:
        raise RuntimeError("Resolution service is not configured")
    return _resolution_service


@router.post("/{case_id}/{requirement_id}")
def resolve_requirement(
        case_id: str,
        requirement_id: str,
        top_k: int = Query(default=8, ge=1, le=20),
):
    try:
        return get_resolution_service().resolve_requirement(
            case_id=case_id,
            requirement_id=requirement_id,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc