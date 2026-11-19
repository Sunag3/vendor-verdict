from fastapi import FastAPI
from src.api.routes.cases import router as cases_router, set_case_service
from src.config.settings import settings
from src.loaders.dataset_loader import VendorVerdictDataset
from src.services.case_service import CaseService

# Register validation service
from src.api.routes.evidence import router as evidence_router, set_validation_service
from src.services.validation_service import ValidationService

# Register chunking service
from src.api.routes.chunks import router as chunks_router, set_chunking_service
from src.services.chunking_service import ChunkingService

# Register Embedding service
from src.rag.embedder import OpenAIEmbedder
from src.rag.vector_store import ChromaVectorStore
from src.rag.retriever import EvidenceRetriever
from src.services.indexing_service import IndexingService
from src.api.routes.indexing import router as indexing_router, set_indexing_service
from src.api.routes.search import router as search_router, set_retriever

# Register retrieval service
from src.rag.requirment_retriever import RequirementRetriever
from src.services.retrieval_service import RetrievalService
from src.api.routes.retrieval import router as retrieval_router, set_retrieval_service


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


validation_service = ValidationService(dataset=dataset)
set_validation_service(validation_service)
app.include_router(evidence_router)


chunking_service = ChunkingService(
    dataset=dataset,
    validation_service=validation_service
)
set_chunking_service(chunking_service)
app.include_router(chunks_router)

# Register Embedding and indexing

embedder = OpenAIEmbedder()

vector_store = ChromaVectorStore()

indexing_service = IndexingService(
    dataset=dataset,
    chunking_service=chunking_service,
    embedder=embedder,
    vector_store=vector_store
)


retriever = EvidenceRetriever(
    embedder=embedder,
    vector_store=vector_store
)
set_indexing_service(indexing_service)
set_retriever(retriever)

app.include_router(indexing_router)
app.include_router(search_router)


# Register retrieval service

requirement_retriever = RequirementRetriever(
    dataset=dataset,
    retriever=retriever
)


retrieval_service = RetrievalService(
    requirement_retriever=requirement_retriever
)


set_retrieval_service(retrieval_service)
app.include_router(retrieval_router)