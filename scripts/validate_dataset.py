from src.loaders.dataset_loader import VendorVerdictDataset

def main():
    dataset = VendorVerdictDataset().load()
    print("Dataset loaded successfully.")
    cases = dataset.cases_df
    print()
    print(
        "="*60
    )
    print("vendor Verdic Dataset Validation")
    print(
        "="*60
    )
    print(f"Total Cases    :{len(cases)}")
    train_count = int((cases['split'] == 'train').sum())
    test_count = int((cases['split'] == 'test').sum())
    print(f"Number of train cases: {train_count}")
    print(f"Number of test cases: {test_count}")
    print(f"Test Cases: {test_count}")
    print(f"Total pages: {len(dataset.pages)}")
    print(f"Requirements: {len(dataset.requirements)}")
    print()
    print("Relationship Validation")
    print("="*60)
    relationship_results = dataset.validate_relationships()
    print("Unknown page cases:", relationship_results.get("unknown_page_cases", []))
    # case without pages
    print("Cases without pages:", relationship_results.get("cases_without_pages", []))
    # Duplicate cases
    print("Duplicate cases:", relationship_results.get("duplicate_case_ids", []))
    print()
    print("="*60)
    first_case_id = cases.iloc[0]['case_id']
    case = dataset.get_case(first_case_id)
    print(f"First case ID: {case.case_id}")
    # vendor
    print(f"Vendor: {case.vendor}")
    # legal entity
    print(f"Legal Entity: {case.legal_entity}")
    # official domain
    print(f"Official Domain: {case.official_domain}")
    # Tier
    print(f"Tier: {case.tier}")
    # Users
    print(f"Users: {case.users}")
    # As-Of
    print(f"As-Of: {case.as_of}")
    # Pages
    print(f"Pages: {case.pages}")
    print("="*60)
    for page in case.pages:
        print(page.page_id, "|", page.source_type, "|", page.url)

if __name__ == "__main__":
    main()
    