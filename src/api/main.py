from fastapi import FastAPI
from src.api.routes.cases import router as cases_router, set_case_service
from src.config.settings import settings
from src.loaders.dataset_loader import VendorVerdictDataset
from src.services.case_service import CaseService


dataset = VendorVerdictDataset().load()
case_service = CaseService(dataset=dataset)
set_case_service(case_service)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Vendor Verdict evidence-driven review API"
)

app.include_router(cases_router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/stats")
def stats():
    return case_service.get_stats()


@app.get("/requirements")
def requirements():
    return case_service.get_requirements()

