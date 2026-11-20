from src.agents.fact_extraction_agent import FactExtractionAgent
from src.agents.prompts import build_fact_extraction_prompt
from src.models.extracted_fact import ExtractedFact
from src.services.retrieval_service import RetrievalService


class FactExtractionService:
    def __init__(self, retrieval_service: RetrievalService, extraction_agent: FactExtractionAgent):
        self.retrieval_service = retrieval_service
        self.extraction_agent = extraction_agent


    def extract_fact_for_requirement(
            self,
            case_id: str,
            requirement_id: str,
            top_k: int = 8
    ) -> ExtractedFact:
        package = (
            self.retrieval_service.retrieve_for_requirement(
                case_id=case_id,
                requirment_id=requirement_id,
                top_k=top_k
            )
        )

        # If chroma found absolutely
        # no trusted evidence,
        # skip Bedrock completely.

        if (package.evidence_count ==0):
            return ExtractedFact(
                field_name=package.field_name,
                missing=True,
                value=None,
                records=[],
                evidence=[],
                notes=(
                    "No trusted evidence retrieved."
                )
            )


        # Build controlled prompt.

        prompt = build_fact_extraction_prompt(package)

        # call strands + Bedrock

        result = self.extraction_agent.extract(prompt)

        # Defensive validation.

        if (
            result.field_name != package.field_name
        ):
            raise ValueError(
                f"Field name mismatch: expected {package.field_name}, got {result.field_name}"
            )

        return result
