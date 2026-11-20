from src.loaders.dataset_loader import VendorVerdictDataset

from src.models.requirement_verdict import RequirementVerdict

from src.policy.rules_adapter import RulesAdapter

from src.services.resolution_service import ResolutionService


class PolicyEvaluationService:

    def __init__(self,
                dataset: VendorVerdictDataset,
                resolution_service: ResolutionService,
                rules_adapter: RulesAdapter
                
                ):
        self.dataset = dataset
        self.rules_adapter = rules_adapter
        self.resolution_service = resolution_service


    def evaluate_requirement(
            self,
            case_id: str,
            requirement_id: str,
            top_k: int = 8,
    ) -> RequirementVerdict:

        requirement = (
            self.dataset.get_requirement(requirement_id)
        )

        resolved = (
            self.resolution_service.resolve_requirement(
                case_id=case_id,
                requirement_id=requirement_id,
                top_k=top_k,
            )
        )

        verdict, reason = (
            self.rules_adapter.evaluate(
                requirement=requirement,
                resolved=resolved,
            )
        )

        return RequirementVerdict(
            case_id=case_id,
            requirement_id=requirement_id,
            requirement_title=requirement['title'],
            field_name=requirement['field'],
            severity=requirement['severity'],
            verdict=verdict,
            resolved_value=resolved.value,
            resolved_records=resolved.records,
            evidence=resolved.evidence,
            reason=reason,
            resolution_status=resolved.resolution_status,
            conflict=resolved.conflict,
        )