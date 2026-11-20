from src.models.resolved_fact import ResolvedFact
from src.resolvers.conflict_resolver import ConflictResolver
from src.services.fact_extraction_service import FactExtractionService

class ResolutionService:

    def __init__(self, extraction_service: FactExtractionService, resolver: ConflictResolver):
        self.extraction_service = extraction_service
        self.resolver = resolver


    def resolve_requirement(
            self,
            case_id: str,
            requirement_id: str,
            top_k: int = 8,
    ) -> ResolvedFact:

        extracted = (
            self.extraction_service
            .extract_fact_for_requirement(
                case_id=case_id,
                requirement_id=requirement_id,
                top_k=top_k,
            )
        )
        return self.resolver.resolve(extracted)

    