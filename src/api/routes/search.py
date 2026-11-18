from fastapi import APIRouter, HTTPException, Query

from src.rag.retriever import EvidenceRetriever

router = APIRouter(
    prefix="/search",
    tags=["search"]
)


_retriever: EvidenceRetriever | None = None

def set_retriever(retriever: EvidenceRetriever):
    global _retriever
    _retriever = retriever


def get_retriever():
    if _retriever is None:
        raise RuntimeError("Retriever not set")
    return _retriever


@router.get("/{case_id}")
def search_case(
    case_id: str,
    q: str = Query(min_length=2),
    top_k: int = Query(default=8, ge=1, le=20)
):
    return (
        get_retriever().retrieve(
            case_id=case_id,
            query=q,
            top_k=top_k
        )
    )