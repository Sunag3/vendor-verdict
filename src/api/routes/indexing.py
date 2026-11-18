from fastapi import APIRouter, HTTPException

from src.services.indexing_service import IndexingService

router = APIRouter(
    prefix="/index",
    tags=["index"]
)

_indexing_service: IndexingService | None = None

def set_indexing_service(service: IndexingService):
    global _indexing_service
    _indexing_service = service


def get_indexing_service():
    if _indexing_service is None:
        raise RuntimeError("Indexing service not set")
    return _indexing_service


@router.post("/case/{case_id}")
def index_case(case_id: str):
    try:
        return get_indexing_service().index_case(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc