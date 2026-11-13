from src.validation.domain_validator import is_official_domain

def test_same_domain():

    assert is_official_domain("https://example.com", "example.com") is True
    assert is_official_domain("https://sub.example.com", "example.com") is True
    assert is_official_domain("https://example.com", "sub.example.com") is False
    assert is_official_domain("https://example.org", "example.com") is False


def test_subdomain():
    assert is_official_domain("https://trust.acme.example", "acme.example")


def test_suffix_attack():
    assert not is_official_domain("https://example.com.evil.com", "example.com")
    assert not is_official_domain("https://example.evil.com", "acme.com")