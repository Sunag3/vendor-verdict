REQUIRMENT_QUERIES = {
    "SEC-4.2": (
        "SOC 2 Type II ISO 27001 "
        "security certification audit "
        "certificate issuer report date "
        "certificate date"
    ),
    "SEC-4.2-T2": (
        "SOC 2 Type I SOC 2 Type II "
        "ISO 27001 security certification "
        "audit questionnaire certificate "
        "issuer report date"
    ),
    "DP-3.1": (
        "customer data stored in India "
        "India data residency "
        "India hosting region "
        "storage location data region"
    ),
    "DP-3.2": (
        "customer data used storage region "
        "data residency hosting location "
        "data region storage location"
    ),
    "AI-2.1": (
        "customer data used for model training "
        "customer content used to train AI "
        "opt out model training "
        "paid plans training"
    ),
    "AI-3.4": (
        "subprocessor sub-processors "
        "third party processors "
        "AI model provider "
        "model providers disclosed"
    ),
    "DP-5.4": (
        "data deletion retention "
        "delete customer data "
        "deletion within days "
        "contract termination "
        "account closure deletion request"
    ),
    "SEC-7.1": (
        "single sign-on SSO SAML OIDC "
        "identity provider IdP "
        "SSO availability plans "
        "enterprise paid plans all plans"
    ),
    "SEC-9.3": (
        "security incident breach outage "
        "major incident critical incident "
        "security event post-mortem "
        "postmortem root cause analysis"
    ),
    "DP-2.2": (
        "data processing agreement DPA "
        "data processiong addendum "
        "DPA available "
        "available on request "
        "data protection agreement"
    )
}


def get_requirement_query(
        requirement_id: str
) -> str:
    query = REQUIRMENT_QUERIES.get(requirement_id, "")

    if not query:
        raise ValueError(
            f"No retrieval query configured"
            f"for requirement ID {requirement_id}"
        )

    return query