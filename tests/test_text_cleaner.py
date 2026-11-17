from src.rag.text_cleaner import split_paragraphs, clean_text


def test_clean_text():
    raw = (
        "Hello   world\r\n"
        "\r\n"
        "\r\n"
        "security   page"
    )

    cleaned = clean_text(raw)

    assert "Hello world" in cleaned
    assert "security page" in cleaned


def test_empty_text():
    assert clean_text(None) == ""
    assert clean_text("") == ""


def test_split_paragraphs():
    text = (
        "First Paragraph.\n\n"
        "Second Paragraph."
    )
    paragraphs = split_paragraphs(text)
    assert len(paragraphs) == 2

    assert split_paragraphs(text) == ["First Paragraph.", "Second Paragraph."]