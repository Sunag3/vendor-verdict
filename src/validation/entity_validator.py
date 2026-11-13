import re

LEGAL_SUFFIXES = {
    "ltd",
    "limited",
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "llc",
    "plc",
    "co",
    "company",
    "gmbh",
    "sarl",
    "bv",
    "oy",
    "pte",
    "pty"
}


def normalize_entity_name(value: str | None) -> str:
    if not value:
        return ""

    # Convert to lowercase and strip whitespace
    value = value.strip().lower()

    # Remove all non-alphanumeric characters except spaces
    value = re.sub(r"[^a-z0-9\s]", "", value)

    tokens = value.split()
    if not tokens:
        return ""

    # Strip legal suffixes ONLY from the end of the token list
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()

    return " ".join(tokens)



def legal_entity_matches(expected_entity: str, publisher: str|None) -> bool:
    expected = normalize_entity_name(expected_entity)
    actual = normalize_entity_name(publisher)

    if not expected or not actual:
        return False

    return expected == actual