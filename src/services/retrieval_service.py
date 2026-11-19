from src.rag.requirment_retriever import RequirementRetriever


class RetrievalService:

    def __init__(self, requirement_retriever: RequirementRetriever):
        self.requirement_retriever = requirement_retriever


    def retrieve_for_requirement(
            self,
            case_id: str,
            requirment_id: str,
            top_k: int = 8
    ):
        return self.requirement_retriever.retrieve(
            case_id=case_id,
            requirment_id=requirment_id,
            top_k=top_k
        )