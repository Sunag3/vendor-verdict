from fastapi import APIRouter, HTTPException, Query
from src.services.case_service import CaseService

router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


_case_service: CaseService | None = None

def set_case_service(service: CaseService):
    global _case_service
    _case_service = service


def get_service() -> CaseService:
    if _case_service is None:
        raise RuntimeError("CaseService is not initialized.")
    return _case_service


@router.get("")
def list_cases(split: str | None = Query(default=None, pattern="^(train|test)$")):
    return get_service().list_cases(split=split)


@router.get("/{case_id}")
def get_case(case_id: str):
    try:
        return get_service().get_case(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{case_id}/pages")
def get_case_pages(case_id: str):
    try:
        return get_service().get_pages(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))