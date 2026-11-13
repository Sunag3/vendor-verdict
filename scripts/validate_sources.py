from collections import Counter

from src.loaders.dataset_loader import VendorVerdictDataset
from src.services.validation_service import ValidationService


def main():
    dataset = VendorVerdictDataset().load()
    service = ValidationService(dataset=dataset)
    total = 0
    usable = 0
    rejected = 0
    injections = 0
    categories = Counter()
    rejection_reasons = Counter()

    for case_id in dataset.cases_df["case_id"]:
        results = service.validate_case(case_id)

        for result in results:
            total+=1
            validation = result.validation
            categories[validation.source_category] += 1
            if validation.usable_evidence:
                usable += 1
            else:
                rejected += 1
                rejection_reasons[validation.rejection_reason] += 1
            if validation.injection_flag:
                injections += 1

    print(f"Total: {total}")
    print(f"Usable: {usable}")
    print(f"Rejected: {rejected}")
    print(f"Injections: {injections}")
    print(f"Categories: {categories}")
    print(f"Rejection Reasons: {rejection_reasons}")


if __name__ == "__main__":
    main()