FIELD_INSTRUCTIONS = {
    "sso_saml": """
Normalize the value exactly one of:
- all_plans
- paid plans
- enterprise_only
- none

Do not infer availability.

If the supplied evidence does not explicitly establish
SSO availability, set missing=true
""",

    "dpa_available": """
Normalize the value to exactly one of:
- yes
- on_request
- no

If the supplied evidence does not explicitly establish
DPA availability, set missing=true
""",

   "trains_on_customer_data": """
Normalize the value to exactly one of:

- no
- no_on_paid_plans
- opt_out_available
- yes

Do not infer from privacy language.

If the supplied evidence does not explicitly establish
behavior, set missing=true
""",
   "data_regions": """
Return explicitly stated customer data-storage
regions as value=list[str]

Example: ["India", "Singapore"]

Do not infer storage location from:
- headquarters
- office location
- company registration country
""",
   "data_retention": """
Return the explicit deletion/retention duration 
in days as value=int.

Example:
30

Do not convert vogue wording such as:
- promptly
- reasonable period
- shortly after termination

into a numeric value.
""",
   "subprocessors": """
Use records.

Each record may contain:
{
    "name": "",
    "category": ""
}

Use category="model_provider" only when evidence
explicitly identifies an AI/model provider.

Do not invent missing subprocessors.
""",
   "security_incidents": """
Use records.

Each incident record should contain when available:

{
    "date": "",
    "severity": "",
    "postmortem_published": true/false
}

Do not decide whether an incident cause policy failure.

Preserve facts only.
""",
   "security_certifications": """
Use records.

Each certification record should contain when available:

{
    "name": "",
    "issuer": "",
    "report_date": "",
    "valid_until": "",
    "evidence_level": "documented" or "claimed"
}

Set evidence_level="documented" only when
both issuer and report/certificate date
are explicitly established by the evidence.

Otherwise use:
evidence_level="claimed"

Do not decide PASS or FAIL.
""",
   

}

def get_field_instruction(field_name: str)->str:
    return FIELD_INSTRUCTIONS.get(field_name, "")