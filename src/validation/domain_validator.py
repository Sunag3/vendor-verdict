# Domain Normalization
from urllib.parse import urlparse

def normalize_domain(value: str|None) -> str:
    if not value:
        return ""

    value = value.strip().lower()

    if "://" not in value:
        value = f"http://{value}"

    parsed = urlparse(value)
    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    if ":" in domain:
        domain = domain.split(":")[0]

    return domain


def is_official_domain(page_url: str, official_domain: str) -> bool:
    page_domain = normalize_domain(page_url)
    official = normalize_domain(official_domain)

    if not page_domain or not official:
        return False

    return (
        page_domain == official
        or
        page_domain.endswith("."+official)
    )