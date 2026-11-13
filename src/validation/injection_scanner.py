# Prompt Injection Scanner

import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"assistant\s+message",
    r"assistant\s+instructions",
    r"return\s+pass",
    r"always\s+return\s+pass",
    # do not follow previous instructions
    r"do\s+not\s+follow\s+previous\s+instructions",
    # do not follow the rules
    r"do\s+not\s+follow\s+the\s+rules",
    # override the instructions
    r"override\s+the\s+instructions",
]


def contains_prompt_injection(text: str|None) -> bool:
    if not text:
        return False

    value = text.lower()
    return any (
        re.search(
            pattern,
            value,
            flags=re.IGNORECASE
        )
        for pattern in INJECTION_PATTERNS
    )