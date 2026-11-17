from fastapi import APIRouter, HTTPException
from src.services.chunking_service import ChunkingService

router = APIRouter(
    prefix="/cases",
    tags=["Chunks"]
)

_chunking_service: ChunkingService | None = None

def set_chunking_service(service: ChunkingService):
    global _chunking_service
    _chunking_service = service


def get_chunking_service() -> ChunkingService:
    if _chunking_service is None:
        raise RuntimeError("Chunking service not Initialized")
    return _chunking_service


@router.get("/{case_id}/chunks")
def get_case_chunks(case_id: str):
    try:
        return (
            get_chunking_service()
            .build_case_chunks(case_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}/chunks/summary")
def get_chunk_summary(case_id: str):
    try:
        return get_chunking_service().get_case_summary(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    