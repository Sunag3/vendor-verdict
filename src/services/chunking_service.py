from src.loaders.dataset_loader import VendorVerdictDataset
from src.models.chunk import EvidenceChunk
from src.rag.chunker import EvidenceChunker
from src.services.validation_service import ValidationService


class ChunkingService:
    def __init__(
            self,
            dataset: VendorVerdictDataset,
            validation_service: ValidationService
    ):
        self.dataset = dataset
        self.validation_service = validation_service

        self.chunker = EvidenceChunker(
            max_words=350,
            overlap_words=40
        )


    def build_case_chunks(self, case_id: str) -> list[EvidenceChunk]:
        evidence_pages = self.validation_service.get_usable_evidence(case_id)
        chunks = []

        for evidence_page in evidence_pages:
            page_chunks = self.chunker.chunk_page(evidence_page)
            chunks.extend(page_chunks)

        return chunks


    def build_all_chunks(self) -> list[EvidenceChunk]:
        chunks = []
        case_ids = self.dataset.cases_df['case_id'].astype(str).tolist()

        for case_id in case_ids:
            case_chunks = self.build_case_chunks(case_id)
            chunks.extend(case_chunks)

        return chunks


    def get_case_summary(self,case_id: str) -> dict:
        validated_pages = self.validation_service.validate_case(case_id)
        usable_pages = [
            item
            for item in validated_pages
            if item.validation.usable_evidence
        ]

        chunks = self.build_case_chunks(case_id)

        return {
            "case_id": case_id,
            "total_pages": len(validated_pages),
            "usable_pages": len(usable_pages),
            "rejected_pages": len(validated_pages) - len(usable_pages),
            "total_chunks": len(chunks),
            "total_chunk_words": sum(chunk.word_count for chunk in chunks)
        }