import re
import unicodedata

def clean_text(text: str|None) -> str:
    if not text:
        return ""
    # Normalize unicode forms
    text = unicodedata.normalize("NFKC", text)

    # Remove Null Bytes
    text = text.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailine spaces from lines
    lines = [
        line.rstrip()
        for line in text.split("\n")
    ]
    text = "\n".join(lines)

    # collapse excessive spaces/tabs,
    # but preserve newlines
    # Remove extra whitespace
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Collaps 3+ blank lines
    # into a maximum of two consecutive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# Paragraph Splitting Helper
def split_paragraphs(text: str) -> list[str]:
    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )
    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]