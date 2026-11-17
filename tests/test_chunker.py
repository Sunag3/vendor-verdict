from src.models.evidence import SourceValidationResult, ValidatedEvidencePage

from src.models.page import VendorPage
from src.rag.chunker import EvidenceChunker

def make_evidence_page(
        usable: bool = True,
):
    page = VendorPage(
        page_id="c0001-p01",
        case_id="c0001",
        url="https://"
            "acme.example/security",
        title="Security",
        source_type="official",
        publisher="Acme",
        published_date="2026-01-01",
        last_updated_date="2026-05-01",
        text = " ".join(
            f"word{i}"
            for i in range(1000)
        ),
    )

    validation = (
        SourceValidationResult(
            page_id="c0001-p01",
            case_id="c0001",
            source_category="official",
            official_domain_match=True,
            legal_entity_match=False,
            certificate_registry_match=False,
            trusted_source=usable,
            usable_evidence=usable,
            injection_flag=False,
            trust_level=(
                "trusted" if usable else "untrusted"
            )
        )
    )

    return ValidatedEvidencePage(
        page=page,
        validation=validation,
    )


def test_chunking():
    chunker = EvidenceChunker(
        max_words=350,
        overlap_words=40,
    )

    chunks = (
        chunker.chunk_page(
            make_evidence_page(),
        )
    )

    assert len(chunks) > 1


def test_chunk_sizes():
    chunker = EvidenceChunker(
        max_words=350,
        overlap_words=40,
    )

    chunks = chunker.chunk_page(make_evidence_page())

    for chunk in chunks:
        assert len(chunk.text.split()) <= 350

    assert all(
        len(chunk.text.split()) <= 350
        for chunk in chunks
    )


def test_chunk_ids_unique():
    chunker = EvidenceChunker(
        max_words=350,
        overlap_words=40,
    )

    chunks = chunker.chunk_page(make_evidence_page())

    ids = [chunk.chunk_id for chunk in chunks]
    assert len(ids) == len(set(ids))


def test_untrusted_page_not_chunker():
    chunker = EvidenceChunker(
        max_words=350,
        overlap_words=40,
    )

    assert chunker.chunk_page(make_evidence_page(usable=False)) == []


# Add Metadata Preservation Tests

def test_chuunk_preserves_metadata():
    chunker = EvidenceChunker()

    chunks = chunker.chunk_page(make_evidence_page())

    chunk = chunks[0]

    assert chunk.page_id == "c0001-p01"
    assert chunk.case_id == "c0001"

    assert chunk.usable_evidence is True

    assert chunk.source_category == "official"

    assert chunk.last_updated == "2026-05-01"

