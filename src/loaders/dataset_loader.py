import json
from collections import defaultdict
from typing import Any

import pandas as pd

from src.config.settings import settings
from src.models.case import VendorCase
from src.models.page import VendorPage

class VendorVerdictDataset:

    def __init__(self):
        self.cases_df: pd.DataFrame | None = None
        self.train_labels_df: pd.DataFrame | None = None
        self.test_df: pd.DataFrame | None = None
        self.sample_submission_df: pd.DataFrame | None = None
        self.pages: list[VendorPage] = []

        self.pages_by_case: dict[
            str,
            list[VendorPage]
        ] = {}

        self.requirements: list[dict[str, Any]] = []


    def load(self) -> "VendorVerdictDataset":
        self._validate_files()
        self._load_cases()
        self._load_pages()
        self._load_requirements()
        self._load_train_labels()
        self._load_test()
        self._load_sample_submission()
        return self


    def _validate_files(self):

        required_files = [
            settings.cases_file,
            settings.pages_file,
            settings.requirements_file,
            settings.train_labels_file,
            settings.test_file,
            settings.sample_submission_file
        ]

        missing = [
            str(path)
            for path in required_files
            if not path.exists()
        ]

        if missing:
            raise FileNotFoundError(
                f"Missing required files: {', '.join(missing)}"
            )


    def _load_cases(self):
        self.cases_df = pd.read_csv(settings.cases_file)
        self.cases_df.fillna("", inplace=True)


    def _load_pages(self):
        pages: list[VendorPage] = []

        with open(settings.pages_file, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)

                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {settings.pages_file}: {e}"
                    )

                try:
                    page = VendorPage(**raw)
                except Exception as exc:
                    raise ValueError(
                        f"Invalid page schema in pages.jsonl on line {line_number}: {exc}"
                    )
                pages.append(page)

            self.pages = pages

            grouped = defaultdict(list)

            for page in pages:
                grouped[page.case_id].append(page)

            self.pages_by_case = dict(grouped)

    def _load_requirements(self):
        with open(settings.requirements_file, "r", encoding="utf-8") as file:
            raw = json.load(file)

        if isinstance(raw, list):
            self.requirements = raw

        elif isinstance(raw, dict):
            if 'requirements' in raw:
                self.requirements = raw['requirements']
            else:
                self.requirements = [raw]
        else:
            raise ValueError(
                "requirements.json must contain a list or a dictionary with a 'requirements' key"
            )


    def _load_train_labels(self):
        self.train_labels_df = pd.read_csv(settings.train_labels_file)
        self.train_labels_df.fillna("", inplace=True)


    def _load_test(self):
        self.test_df = pd.read_csv(settings.test_file)
        self.test_df.fillna("", inplace=True)


    def _load_sample_submission(self):
        self.sample_submission_df = pd.read_csv(settings.sample_submission_file)
        self.sample_submission_df.fillna("", inplace=True)


    @staticmethod
    def _clean_row(row: dict) -> dict:
        cleaned = {}
        for key, value in row.items():
            if pd.isna(value):
                cleaned[key] = None
            else:
                cleaned[key] = value

        return cleaned


    def get_case(self, case_id: str) -> VendorCase:
        if self.cases_df is None:
            raise RuntimeError("Data Set Cases data is not loaded.")

        rows = self.cases_df[self.cases_df['case_id'] == case_id]

        if rows.empty:
            raise ValueError(f"Case with case_id '{case_id}' not found in the dataset.")

        row = self._clean_row(rows.iloc[0].to_dict())

        if not row.get('users') is not None:
            row['users'] = int(row['users'])

        pages = self.pages_by_case.get(case_id, [])

        return VendorCase(**row, pages=pages)


    def get_cases(self, split: str | None = None) -> list[VendorCase]:
        if self.cases_df is None:
            raise RuntimeError("Data Set Cases data is not loaded.")

        df = self.cases_df

        if split:
            df = df[df['split'] == split]

        return [self.get_case(case_id) for case_id in df['case_id']]


    def get_test_cases(self) -> list[VendorCase]:
        return self.get_cases(split="test")


    def get_requirements(self) -> list[dict]:
        return self.requirements


    def validate_relationships(self) -> dict:
        case_ids = set(self.cases_df['case_id'].astype(str))

        page_case_ids = set(page.case_id for page in self.pages)

        unknown_page_cases = (
            page_case_ids - case_ids
        )

        cases_without_pages = [
            case_id
            for case_id in case_ids
            if case_id
            not in self.pages_by_case
        ]

        duplicate_case_ids = (
            self.cases_df[self.cases_df["case_id"].duplicated(keep=False)]["case_id"].astype(str).tolist()
        )

        return {
            "unknown_page_cases": sorted(unknown_page_cases),
            "cases_without_pages": sorted(cases_without_pages),
            "duplicate_case_ids": sorted(duplicate_case_ids)
        }