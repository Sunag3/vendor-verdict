# Chunker Implementation

import hashlib
from src.models.chunk import EvidenceChunk
from src.rag.text_cleaner import split_paragraphs, clean_text
from src.models.evidence import ValidatedEvidencePage


class EvidenceChunker:
    def __init__(
            self,
            max_words: int=350,
            overlap_words: int=40
        ):
        if max_words <= 0:
            raise ValueError("max_words must be greater than 0")
        if overlap_words<0:
            raise ValueError("overlap_words must be greater than or equal to 0")
        if overlap_words>=max_words:
            raise ValueError("overlap_words must be less than max_words")
        self.max_words = max_words
        self.overlap_words = overlap_words


    def chunk_page(
            self,
            evidence_page: ValidatedEvidencePage
    )-> list[EvidenceChunk]:
        validation = evidence_page.validation

        page = evidence_page.page

        # Strong safety Boundry
        if not validation.usable_evidence:
            return []

        cleaned_text = clean_text(page.text)

        if not cleaned_text:
            return []

        raw_chunks = (
            self._split_text(cleaned_text)
        )

        total_chunks = len(raw_chunks)

        chunks = []

        for index, item in enumerate(raw_chunks):
            chunk_text = item["text"]
            content_hash = self._content_hash(chunk_text)
            chunk_id = f"{page.page_id}-chunk-{index:03d}"
            chunks.append(
                EvidenceChunk(
                    chunk_id=chunk_id,
                    case_id=page.case_id,
                    page_id=page.page_id,
                    chunk_index=index,
                    total_chunks=total_chunks,
                    text=chunk_text,
                    word_count=len(chunk_text.split()),
                    start_word=item["start_word"],
                    end_word=item["end_word"],
                    content_hash=content_hash,
                    url=page.url,
                    title=page.title,
                    source_type=page.source_type,
                    publisher=page.publisher,
                    published_date=page.published_date,
                    last_updated=page.last_updated,
                    source_category=validation.source_category,
                    official_domain_match=validation.official_domain_match,
                    legal_entity_match=validation.legal_entity_match,
                    certificate_registry_match=validation.certificate_registry_match,
                    trusted_source=validation.trusted_source,
                    usable_evidence=validation.usable_evidence,
                    trust_level=validation.trust_level,
                    injection_flag=validation.injection_flag,
                )
            )

        return chunks


    # def _split_text(self, text:str) -> list[dict]:
    #     paragraphs = (
    #         split_paragraphs(text)
    #     )

    #     # Flatten paragraphs into words
    #     # while keeping natural ordering
    #     all_words = []
    #     for paragraph in paragraphs:
    #         words = paragraph.split()
    #         if not words:
    #             continue
    #         all_words.extend(words)

    #     if not all_words:
    #         return []
    #     chunks = []
    #     start = 0
    #     total_words = len(all_words)

    #     while start < total_words:
    #         end = min(start + self.max_words, total_words)
    #         words = all_words[start:end]
    #         chunk_text = " ".join(words)
    #         chunks.append(
    #             {
    #                 "text": chunk_text,
    #                 "start_word": start,
    #                 "end_word": end - 1
    #             }
    #         )
    #         if end >= total_words:
    #             break
    #         start = end - self.overlap_words
    #     return chunks


    @staticmethod
    def _content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Paragraph aware splitting
    def _split_text(self, text: str) -> list[dict]:
        paragraphs = split_paragraphs(text)

        if not paragraphs:
            return []

        chunks: list[dict] = []
        current_words: list[str] = []

        global_word_position = 0
        chunk_start_word = 0

        for paragraph in paragraphs:
            paragraph_words = paragraph.split()

            if not paragraph_words:
                continue

            # very large paragraph
            # split internally.

            if len(paragraph_words) > self.max_words:
                if current_words:
                    chunks.append(
                        {
                            "text": " ".join(current_words),
                            "start_word": chunk_start_word,
                            "end_word":  (
                                chunk_start_word + len(current_words) - 1
                            )
                        }
                    )
                    current_words = []
                
                local_start = 0
                while local_start < len(paragraph_words):
                    local_end = min(local_start + self.max_words, len(paragraph_words))
                    words = paragraph_words[local_start:local_end]
                    absolute_start = (
                        global_word_position + local_start
                    )
                    chunks.append(
                        {
                            "text": " ".join(words),
                            "start_word": absolute_start,
                            "end_word": absolute_start + len(words) - 1
                        }
                    )

                    if (local_end >= len(paragraph_words)):
                        break
                    local_start = local_end - self.overlap_words

                global_word_position += len(paragraph_words)
                chunk_start_word = global_word_position
                continue

            projected_size = (
                len(current_words) + len(paragraph_words)
            )

            if (current_words and projected_size > self.max_words):
                chunks.append(
                    {
                        "text": " ".join(current_words),
                        "start_word": chunk_start_word,
                        "end_word": chunk_start_word + len(current_words) - 1
                    }
                )

                overlap = (
                    current_words[-self.overlap_words:] if self.overlap_words else []
                )
                # Do not let overlap make the next
                # chunk exceeds max_words due to overlap, adjust accordingly
                if (
                    len(overlap)
                    + len(paragraph_words) > self.max_words
                ):
                    overlap = []

                current_words = list(overlap)

                chunk_start_word = global_word_position - len(overlap)

            current_words.extend(paragraph_words)
            global_word_position += len(paragraph_words)

        if current_words:
            chunks.append(
                {
                    "text": " ".join(current_words),
                    "start_word": chunk_start_word,
                    "end_word": chunk_start_word + len(current_words) - 1
                }
            )
        return chunks
