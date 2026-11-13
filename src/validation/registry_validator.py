CERTIFICATE_SOURCE_TYPES = {
    "certificate_registry",
    "cert_registry",
    "registry"
}

def is_certificate_registry(source_type: str | None) -> bool:
    if not source_type:
        return False

    return (
        source_type
        .strip()
        .lower() in CERTIFICATE_SOURCE_TYPES
    )
