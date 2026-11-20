from datetime import date
from typing import Any


from src.config.settings import settings

from src.models.extracted_fact import (
    ExtractedFact,
    FactCandidate,
    EvidenceReference,
)

from src.models.resolved_fact import ResolvedFact


COMPLEX_FIELDS = {
    "security_certifications",
    "security_incidents",
    "subprocessors"
}


class ConflictResolver:

    def __init__(
            self,
            as_of_date: date | None = None,
    ):
        self.as_of_date = as_of_date or settings.as_of_date


    def resolve(
            self,
            extracted: ExtractedFact,
    ) -> ResolvedFact:
        # keep only candidates valid as of completion date.

        candidates, ignored_count = (
            self._filter_as_of(
                extracted.candidates
            )
        )

        # No structured candidates

        if not candidates:

            return self._fallback_without_candidates(extracted=extracted, ignored_count=ignored_count)


        # COMPLEX FIELDS
        if (
            extracted.field_name in COMPLEX_FIELDS
        ):
            return self._resolve_complex(
                extracted=extracted,
                candidates=candidates,
                ignored_count=ignored_count,
            )


        # Simple scalar or list fields
        return self._resolve_simple(
            extracted=extracted,
            candidates=candidates,
            ignored_count=ignored_count,
        )


    def _filter_as_of(
            self,
            candidates: list[FactCandidate],
    ) -> tuple[list[FactCandidate], int]:
        valid = []
        ignored = 0

        for candidate in candidates:
            source_date = (
                self._parese_date(
                    candidate.last_updated
                )
            )

            # No date
            # keep it rather than inventing one.

            if source_date is None:
                valid.append(candidate)
                continue

            if source_date > self.as_of_date:
                ignored += 1
                continue

            valid.append(candidate)

        return valid, ignored


    @staticmethod
    def _parese_date(value: str | None) -> date | None:
        if value is None:
            return None

        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


    def _resolve_simple(
            self,
            extracted: ExtractedFact,
            candidates: list[FactCandidate],
            ignored_count: int,
    ) -> ResolvedFact:
        candidates = [
            candidate
            for candidate in candidates
            if candidate.value is not None
        ]

        if not candidates:
            return ResolvedFact(
                field_name=extracted.field_name,
                missing=True,
                value=None,
                evidence=[],
                resolution_status="missing",
                ignored_future_candidates=ignored_count,
            )

        # Sort the newest first

        ordered = sorted(
            candidates,
            key = self._candidate_sort_key,
            reverse=True,
        )

        newest_date = (
            self._candidate_sort_key(ordered[0])
        )

        # Find all candidates having the same newest date

        newest_candidates = [
            candidate
            for candidate in ordered
            if self._candidate_sort_key(candidate) == newest_date
        ]


        normalized_values = {
            self._normalize_comparable(
                candidate.value
            )
            for candidate in newest_candidates
        }

        # For same date + different values
        # dont guess

        if len(normalized_values) > 1:
            return ResolvedFact(
                field_name=extracted.field_name,
                missing=False,
                value=None,
                records=[],
                evidence=self._build_evidence(
                    extracted,
                    newest_candidates,
                ),
                resolution_status="unresolved_conflict",
                conflict=True,
                ignored_future_candidates=ignored_count,
                notes=(
                    "conflicting values have same latest last_updated date"
                )
            )

        winner = newest_candidates[0]

        return ResolvedFact(
            field_name=extracted.field_name,
            missing=False,
            value=self._normalize_value(
                extracted.field_name,
                winner.value,
            ),
            records=[],
            evidence=self._build_evidence(
                extracted,
                [winner],
            ),
            resolution_status="resolved",
            conflict=len({
                self._normalize_comparable(candidate.value)
                for candidate in candidates
            }) > 1,
            ignored_future_candidates=ignored_count,
        )


    def _candidate_sort_key(self, candidate: FactCandidate) -> date:
        parsed = self._parese_date(candidate.last_updated)

        # Unknown date sorts oldest

        return parsed or date.min


    @staticmethod
    def _normalize_comparable(value: Any) -> str:

        if isinstance(value, list):
            return "|".join(
                sorted(
                    str(item).strip().lower() for item in value
                )
            )
        return str(value).strip().lower()


    def _normalize_value(self, field_name: str, value: Any) -> Any:

        if value is None:
            return None

        if isinstance(value, str):
            return (
                value
                .strip()
                .lower()
                .replace(" ", "_")
            )

        if isinstance(value, list):
            cleaned = []

            seen = set()

            for item in value:
                text = (
                    str(item)
                    .strip()
                )

                key = text.lower()

                if key in seen:
                    continue

                seen.add(key)
                cleaned.append(text)

            return cleaned

        return value


    def _resolve_complex(
            self,
            extracted: ExtractedFact,
            candidates: list[FactCandidate],
            ignored_count: int,
    ) -> ResolvedFact:

        candidates = [
            candidate
            for candidate in candidates
            if candidate.record
        ]

        if not candidates:
            return ResolvedFact(
                field_name=extracted.field_name,
                missing=True,
                value=None,
                records=[],
                evidence=[],
                resolution_status="missing",
                conflict=False,
                ignored_future_candidates=ignored_count,
            )

        if extracted.field_name == "security_certifications":
            records = self._resolve_certifications(candidates)

        elif extracted.field_name == "security_incidents":
            records = self._resolve_records_by_key(
                candidates,
                key_name="date"
            )


        elif extracted.field_name == "subprocessors":
            records = (
                self._resolve_records_by_key(
                    candidates,
                    key_name="name"
                )
            )

        else:
            records = [
                candidate.record
                for candidate in candidates
                if candidate.record
            ]


        return ResolvedFact(
            field_name=extracted.field_name,
            missing=len(records) == 0,
            value=None,
            records=records,
            evidence=self._build_evidence(extracted, candidates),
            resolution_status="resolved" if records else "missing",
            conflict=False,
            ignored_future_candidates=ignored_count,
        )


    def _resolve_certifications(
            self,
            candidates: list[FactCandidate],
    ) -> list[dict[str, Any]]:


        grouped: dict[
            str,
            list[FactCandidate]
        ] = {}

        for candidate in candidates:
            record = candidate.record or {}

            name = record.get("name", "").strip()
            if not name:
                continue

            key = self._normalize_cert_name(
                name
            )

            grouped.setdefault(key, []).append(candidate)

        resolved = []

        for certification_name, group in grouped.items():
            ordered = sorted(
                group,
                key=self._candidate_sort_key,
                reverse=True
            )

            winner = ordered[0]

            record = dict(winner.record or {})
            record["name"] = certification_name
            issuer = (record.get('issuer'))
            report_date = record.get("report_date")

            # Determistic enforcement

            if issuer and report_date:
                record['evidence_level'] = "documented"

            else:
                record['evidence_level'] = "claimed"

            resolved.append(record)

        return resolved


    @staticmethod
    def _normalize_cert_name(name: str) -> str:
        normalized = name.strip().lower()

        if ("soc 2" in normalized and "type ii" in normalized):
            return "SOC 2 Type II"

        if ("soc 2" in normalized and "type i" in normalized):
            return "SOC 2 Type I"

        if 'iso' in normalized and '27001' in normalized:
            return "ISO 27001"

        return name.strip()


    def _resolve_records_by_key(
            self,
            candidates: list[FactCandidate],
            key_name: str
    )->list[dict[str, Any]]:
        grouped: dict[str, list[FactCandidate]] = {}

        for candidate in candidates:
            record = candidate.record or {}
            key_value = record.get(key_name)
            if not key_value:
                continue

            key = str(key_value).strip().lower()
            
            grouped.setdefault(key, []).append(candidate)

        resolved = []

        for group in grouped.values():
            ordered = sorted(
                group,
                key=self._candidate_sort_key,
                reverse=True
            )

            winner = ordered[0]
            if winner.record:
                resolved.append(
                    dict(winner.record)
                )

        return resolved


    @staticmethod
    def _build_evidence(
        extracted: ExtractedFact,
        candidates: list[FactCandidate],
    ) -> list[EvidenceReference]:
        wanted = {
            (
                candidate.page_id,
                candidate.chunk_id
            )
            for candidate in candidates
        }

        return [
            evidence
            for evidence in extracted.evidence
            if (evidence.page_id, evidence.chunk_id) in wanted
        ]


    def _fallback_without_candidates(
            self,
            extracted: ExtractedFact,
            ignored_count: int
    ) -> ResolvedFact:

        if extracted.missing:
            return ResolvedFact(
                field_name=extracted.field_name,
                missing=True,
                value=None,
                records=[],
                evidence=[],
                resolution_status="missing",
                conflict=False,
                ignored_future_candidates=ignored_count,
                notes=("Extraction returned no candidate facts")
            )

        # Temporary backward compatibility.
        # one step 6 candidates are working,
        # this path should rarely be used.

        return ResolvedFact(
            field_name=extracted.field_name,
            missing=False,
            value=self._normalize_value(
                extracted.field_name,
                extracted.value,
            ),
            records=extracted.records,
            evidence=extracted.evidence,
            resolution_status="resolved",
            conflict=False,
            ignored_future_candidates=ignored_count,
            notes="Resolved from legacy step6 output without candidates."
        )