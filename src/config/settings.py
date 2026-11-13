from datetime import date
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Vendor Verdict API"
    app_version: str = "0.1.0"
    app_env: str = "development"

    data_dir: str = "data"
    output_dir: str = "outputs"

    as_of_date: date = date(2026, 11, 1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_path(self) -> Path:
        return self.base_dir / self.data_dir

    @property
    def cases_file(self) -> Path:
        return self.data_path / "cases.csv"

    @property
    def pages_file(self) -> Path:
        return self.data_path / "pages.jsonl"

    @property
    def requirements_file(self) -> Path:
        return self.data_path / "requirements.json"

    @property
    def train_labels_file(self) -> Path:
        return self.data_path / "train_labels.csv"

    @property
    def test_file(self) -> Path:
        return self.data_path / "test.csv"

    @property
    def sample_submission_file(self) -> Path:
        return self.data_path / "sample_submission.csv"

    @property
    def rules_file(self) -> Path:
        return self.data_path / "rules_lite.py"

    @property
    def metrics_file(self) -> Path:
        return self.data_path / "metrics.py"

settings = Settings()