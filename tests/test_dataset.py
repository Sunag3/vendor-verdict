import pytest
from src.loaders.dataset_loader import VendorVerdictDataset

@pytest.fixture(scope="module")
def dataset():
    return VendorVerdictDataset().load()


def test_dataset_loads(dataset):
    assert dataset.cases_df is not None
    assert len(dataset.cases_df) > 0
    assert dataset.pages is not None
    assert len(dataset.pages) > 0


def test_case_lookup(dataset):
    case_id = dataset.cases_df.iloc[0]['case_id']
    case = dataset.get_case(case_id)
    assert case.case_id == case_id
    assert len(case.pages) > 0