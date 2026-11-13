from fastapi import APIRouter, HTTPException
from typing import Optional

from src.services.validation_service import ValidationService

router = APIRouter(
    prefix="/cases",
    tags=["Evidence"],
)

_validation_service: ValidationService
_validation_service = None


def set_validation_service(service: ValidationService):
    service: ValidationService
    global _validation_service
    _validation_service = service


def get_validation_service() -> ValidationService:
    if _validation_service is None:
        raise RuntimeError("Validation service is not initialized")
    return _validation_service


@router.get("/{case_id}/evidence")
def get_case_evidence(case_id: str):
    try:
        return (
            get_validation_service().validate_case(case_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{case_id}/evidence/usable")
def get_usable_evidence(case_id: str):
    try:
        return (get_validation_service()
                .get_usable_evidence(case_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc