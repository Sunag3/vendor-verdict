from src.loaders.dataset_loader import VendorVerdictDataset
from src.models.evidence import ValidatedEvidencePage
from src.validation.source_validator import SourceValidator

class ValidationService:
    def __init__(self, dataset: VendorVerdictDataset):
        self.dataset = dataset
        self.validator = SourceValidator()

    def validate_case(self, case_id: str) -> list[ValidatedEvidencePage]:
        case = self.dataset.get_case(case_id)
        results = []

        for page in case.pages:
            validation = self.validator.validate(case, page)
            results.append(
                ValidatedEvidencePage(
                    page=page,
                    validation=validation
                )
            )
        return results


    def get_usable_evidence(self, case_id: str) -> list[ValidatedEvidencePage]:
        results = self.validate_case(case_id)
        return [
            result
            for result in results
            if (
                result
                .validation
                .usable_evidence
            )
        ]