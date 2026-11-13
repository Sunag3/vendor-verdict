# Source Type classification

TRUSTED_SOURCE_TYPES = {
    "official",
    "vendor",
    "vendor_official",
    "certificate_registry",
    "cert_registry"
}

UNTRUSTED_SOURCE_TYPES = {
    "review",
    "reviews",
    "news",
    "forum",
    "community",
    "blog",
    "social_media",
    "directory",
    "social"
}


from src.models.case import VendorCase
from src.models.page import VendorPage
from src.models.evidence import SourceValidationResult

from src.validation.domain_validator import is_official_domain
from src.validation.entity_validator import legal_entity_matches
from src.validation.registry_validator import is_certificate_registry
from src.validation.injection_scanner import contains_prompt_injection

class SourceValidator:

    def validate(self, case: VendorCase, page: VendorPage) -> SourceValidationResult:

            source_type = (page.source_type or "").strip().lower()

            official_match = is_official_domain(page.url, case.official_domain)
            entity_match = legal_entity_matches(case.legal_entity, page.publisher)
            registry_match = is_certificate_registry(page.source_type)
            injection_flag = contains_prompt_injection(page.text)

            source_category = self._classify_source(
                source_type=source_type,
                official_match=official_match,
                registry_match=registry_match
            )

            trusted_source = False
            usable_evidence = False
            trust_level = 'untrusted'
            rejection_reason = None

            # 🚨 CRITICAL FIX: Prompt injection overrides everything else
            if injection_flag:
                rejection_reason = 'Prompt injection detected in source text'
            
            # Rule 1: Vendor Official domain
            elif official_match:
                trusted_source = True
                usable_evidence = True
                trust_level = 'trusted'

            # Rule 2: Certificate registry + matching legal entity
            elif registry_match and entity_match:
                trusted_source = True
                usable_evidence = True
                trust_level = 'trusted'

            # Explicit third-party sources
            elif source_type in UNTRUSTED_SOURCE_TYPES:
                rejection_reason = 'Third-party source cannot establish vendor facts'

            # Registry but wrong entity
            elif registry_match and not entity_match:
                rejection_reason = 'Certificate registry entry does not match legal entity'

            # Everything else
            else:
                rejection_reason = 'Source is not an approved evidence source'

            return SourceValidationResult(
                page_id=page.page_id,
                case_id=case.case_id,
                source_category=source_category,
                official_domain_match=official_match,
                legal_entity_match=entity_match,
                certificate_registry_match=registry_match,
                injection_flag=injection_flag,
                trusted_source=trusted_source,
                usable_evidence=usable_evidence,
                trust_level=trust_level,
                rejection_reason=rejection_reason  # Matches your model field name
            )

    @staticmethod
    def _classify_source(
        source_type: str,
        official_match: bool,
        registry_match: bool
    ) -> str:
        if official_match:
            return 'official'
        if registry_match:
            return 'certificate_registry'
        if source_type:
            return source_type
        return 'unknown'