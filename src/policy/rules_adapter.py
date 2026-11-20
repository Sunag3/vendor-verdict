from datetime import date
from typing import Any

from src.models.resolved_fact import (
    ResolvedFact,
)
from calendar import monthrange


class RulesAdapter:

    def __init__(self, as_of_date: date):
        self.as_of_date = as_of_date


    def evaluate(
            self,
            requirement: dict,
            resolved: ResolvedFact,
            
    ) -> tuple[str, str]:
        # Rule engine should never receive
        # unresolved conflicting evidence
        # as a definite fact.

        if (
            resolved.resolution_status == "unresolved_conflict"
        ):
            return (
                "NEEDS_REVIEW",
                "Latest trusted evidence contains "
                "an unresolved conflict."
            )


        # Missing evidence

        if resolved.missing:
            return (
                "UNKNOWN",
                "No trusted evidence established "
                "the required fact."
            )

        rule_name = requirement["rule"]

        params = requirement.get("params", {})

        field_name = requirement.get("field")

        # Dispatch by authoritative rule name

        if rule_name == "enum_verdict":

            return self._enum_verdict(
                value=resolved.value,
                params=params,
            )

        if rule_name == "value_known":
            return self._value_known(
                value=resolved.value
            )

        if rule_name == "region_includes":
            return self._region_includes(
                value=resolved.value,
                params=params,
            )

        if rule_name == "retention_within":
            return self._retention_within(
                value=resolved.value,
                params=params,
            )


        if rule_name == "list_disclosed":
            return self._list_disclosed(
                value=resolved.value,
                params=params,
            )

        if rule_name == "certification_valid":
            return self._certification_valid(
                value=resolved.value,
                params=params,
            )

        if rule_name == "no_unresolved_incident":
            return self._no_unresolved_incident(
                value=resolved.value,
                params=params,
            )


        raise ValueError(f"Unsupported rule: {rule_name} for field {field_name}")


    @staticmethod
    def _enum_verdict(
        value: Any,
        params: dict,
    ) -> tuple[str, str]:

        if value is None:
            return (
                "UNKNOWN",
                "Required value is missing."
            )

        if isinstance(value, list):
            value = value[0] if len(value) == 1 else None
            if value is None:
                return ("UNKNOWN", "Required value is missing.")

        pass_values = set(
            params.get("pass", [])
        )

        review_values = set(
            params.get("review", [])
        )

        fail_values = set(
            params.get("fail", [])
        )

        if value in pass_values:
            return (
                "PASS",
                f"Value '{value}' satisfies the policy rule."
            )

        if value in review_values:
            return (
                "NEEDS_REVIEW",
                f"Value '{value}' requires manual review."
            )

        if value in fail_values:
            return (
                "FAIL",
                f"Value '{value}' violates the policy rule."
            )

        return (
            "UNKNOWN",
            f"Value '{value}' is not recognized by the policy rule."
        )

    @staticmethod
    def _value_known(
        value: Any,
    ) -> tuple[str, str]:

        if value is None:
            return (
                "UNKNOWN",
                "The Required value is not known."
            )

        if isinstance(value, list) and not value:
            return (
                "UNKNOWN",
                "The Required list is empty."
            )

        return (
            "PASS",
            "The required value is documented."
        )

    @staticmethod
    def _region_includes(
        value: Any,
        params: dict,
    ) -> tuple[str, str]:

        if value is None:
            return (
                "UNKNOWN",
                "No trusted data-region information is available."
            )

        if not isinstance(value, list):
            return (
                "UNKNOWN",
                "The Data-region value has an unexpected format."
            )
        
        required_regions = {
            str(region).strip().lower()
            for region in params.get("any_of", [])
        }

        actual_regions = {
            str(region).strip().lower()
            for region in value
        }

        matched = required_regions & actual_regions

        if matched:
            return (
                "PASS",
                "Required storage region is available: "
                + ", ".join(sorted(matched))
            )

        return (
            "FAIL",
            "Required storage region is not present in the documented regions."
        )

    
    @staticmethod
    def _retention_within(
        value: Any,
        params: dict,
    ) -> tuple[str, str]:
        if value is None:
            return (
                "UNKNOWN",
                "No explicit retention/deletion period is documented"
            )

        if not isinstance(value, (int, float)):
            return (
                "UNKNOWN",
                "The Retention value is not numeric."
            )

        max_days = params.get("max_days")
        if max_days is None:
            return (
                "UNKNOWN",
                "retention_within requires params.max_days."
            )

        if value <= max_days:
            return (
                "PASS",
                f"The documented deletion period {value} days is within the maximum of {max_days}-day limit."
            )

        return (
            "FAIL",
            f"The documented deletion period {value} days exceeds the maximum of {max_days}-day limit."
        )


    @staticmethod
    def _list_disclosed(
        records: list[dict],
        params: dict,
    ) -> tuple[str, str]:
        if not records:
            return (
                "UNKNOWN",
                "No trusted subprocessor list was established."
            )

        review_categories = {
            str(category).strip().lower()
            for category in params.get("review_if_category", [])
        }

        for record in records:
            category = (
                str(record.get("category", "")).strip().lower()
            )

            if category in review_categories:
                return (
                    "NEEDS_REVIEW",
                    f"Subprocessor disclosure includes category '{category}'."
                )

        return (
            "PASS",
            "Subprocessors are disclosed and no configured review category was found."
        )


    def _certification_valid(
            self,
            records: list[dict],
            params: dict,
    ) -> tuple[str, str]:

        if not records:
            return (
                "UNKNOWN",
                "No trusted security certification was established."
            )

        accepted = {
            str(item).strip().lower()
            for item in params.get("accepted", [])
        }

        max_age_months = params.get("max_age_months")

        require_documented = bool(
            params.get("require_documented", False)
        )

        matching_found = False

        for record in records:
            name = (
                str(
                    record.get("name", "")
                ).strip()
            )

            if (name.lower() not in accepted):
                continue

            matching_found = True

            evidence_level = (
                str(
                    record.get("evidence_level", "")
                ).strip().lower()
            )

            if require_documented and evidence_level != "documented":
                continue

            report_date = (
                self._parse_date(record.get("report_date", ""))
            )

            if max_age_months is not None:
                if report_date is None:
                    continue

                age_months = (
                    self._months_between(report_date, self.as_of_date)
                )

                if age_months > max_age_months:
                    continue

            return (
                "PASS",
                f"Valid accepted certification found: '{name}'."
            )

        if matching_found:
            return (
                "NEEDS_REVIEW",
                "Accepted certification was found but documentation/date requirements were not fully satisfied."
            )

        return (
            "FAIL",
            "No accepted security certification was found."
        )



    # Add date helpers
    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date | None:
        if not value:
            return None

        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


    @staticmethod
    def _months_between(
        start: date,
        end: date,
    ) -> int:
        months = (
            end.year - start.year
        ) * 12 + end.month - start.month

        if end.day < start.day:
            months -= 1
        return max(
            months,
            0,
        )

    def _no_unresolved_incident(
            self,
            records: list[dict],
            params: dict,
    ) -> tuple[str, str]:

        if not records:
            return (
                "PASS",
                "No qualifying security incident was established."
            )

        lookback_months = params.get("lookback_months", 24)
        major_severities = {
            str(item).strip().lower()
            for item in params.get("major_severities", [])
        }


        for incident in records:
            incident_date = (
                self._parse_date(incident.get("date", ""))
            )

            if incident_date is None:
                continue

            age_months = (
                self._months_between(incident_date, self.as_of_date)
            )


            if age_months > lookback_months:
                continue

            severity = (
                str(incident.get("severity", "")).strip().lower()
            )

            if severity not in major_severities:
                continue

            postmortem = (
                incident.get("postmortem_published", "")
            )

            if postmortem is True:
                return (
                    "NEEDS_REVIEW",
                    "A recent major/critical incident exists, but a post-mortem was published."
                )

            return (
                "FAIL",
                f"A recent major/critical incident exists without a published post-mortem."
            )

        return (
            "PASS",
            f"No major critical incident within the configured lookback period violates the rule."
        )

    
