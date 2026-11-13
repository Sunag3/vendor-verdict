from pydantic import BaseModel

class DatasetStats(BaseModel):
    total_cases: int
    train_cases: int
    test_cases: int

    total_pages: int
    total_requirements: int