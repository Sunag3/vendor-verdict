from src.loaders.dataset_loader import VendorVerdictDataset

class CaseService:
    
    def __init__(self, dataset: VendorVerdictDataset):
        self.dataset = dataset

    def list_cases(self, split: str | None = None):
        cases = self.dataset.get_cases(
            split=split
        )

        return [
            {
                "case_id": case.case_id,
                "split": case.split,
                "vendor": case.vendor,
                "legal_entity": case.legal_entity,
                "official_domain": case.official_domain,
                "tier": case.tier,
                "users": case.users,
                "as_of": case.as_of,
                "page_count": len(case.pages)
            }
            for case in cases
        ]


    def get_case(self, case_id: str):

        return (self.dataset.get_case(case_id))


    def get_pages(self, case_id: str):
        case = self.dataset.get_case(case_id)

        return case.pages


    def get_requirements(self):
        return self.dataset.get_requirements()


    def get_stats(self):
        cases = (
            self.dataset.cases_df
        )

        return {
            "total_cases": len(cases),
            "train_cases": int((cases["split"] == "train").sum()),
            "test_cases": int((cases["split"] == "test").sum()),
            "total_pages": len(self.dataset.pages),
            "total_requirements": len(self.dataset.requirements),
        }