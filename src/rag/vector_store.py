import chromadb

from src.models.chunk import EvidenceChunk
from src.config.settings import settings

class ChromaVectorStore:

    def __init__(
            self,
            collection_name: str | None = None
    ):

        settings.chroma_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.chroma_db_path))
        self.collection_name = collection_name or settings.chroma_collection

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Evidence chunks for RAG retrieval"
                },
            )
        )


    def count(self) -> int:
        return self.collection.count()


    @staticmethod
    def _chunk_metadata(chunk: EvidenceChunk) -> dict:

        metadata = {
            "case_id": chunk.case_id,
            "page_id": chunk.page_id,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            "word_count": chunk.word_count,
            "start_word": chunk.start_word,
            "end_word": chunk.end_word,
            "content_hash": chunk.content_hash,
            "url": chunk.url,
            "source_category": chunk.source_category,
            "official_domain_match": chunk.official_domain_match,
            "legal_entity_match": chunk.legal_entity_match,
            "certificate_registry_match": chunk.certificate_registry_match,
            "trusted_source": chunk.trusted_source,
            "usable_evidence": chunk.usable_evidence,
            "trust_level": chunk.trust_level,
            "injection_flag": chunk.injection_flag,
            "embedding_model": settings.openai_embedding_model
        }

        optional_fields = {
            "title": chunk.title,
            "source_type": chunk.source_type,
            "publisher": chunk.publisher,
            "published_date": chunk.published_date,
            "last_updated": chunk.last_updated
        }

        for key, value in optional_fields.items():
            if value is not None:
                metadata[key] = str(value)

        return metadata


    # Add chunks to Chroma DB

    def add_chunks(
            self,
            chunks: list[EvidenceChunk],
            embeddings: list[list[float]]
    ):
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks must match the number of embeddings.")

        for chunk in chunks:
            if not chunk.usable_evidence:
                raise ValueError(
                    f"Attempted to index"
                    f"Untrusted chunk: "
                    f"{chunk.chunk_id}"
                )

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[self._chunk_metadata(chunk) for chunk in chunks],
            embeddings=embeddings
        )


    # Add a query Support
    def query(
            self,
            query_embedding: list[float],
            case_id: str,
            n_results: int = 10
    ) -> dict:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                "$and": [
                    {"case_id": case_id},
                    {"usable_evidence": True}
                ]
            },
            include=["documents", "metadatas", "distances"]
        )


    # Add deletion helpers

    def delete_case(
            self,
            case_id: str
    ):
        self.collection.delete(where={"case_id": case_id})


    # Reset Helpers

    def reset_collection(self) -> None:
        try:
            self.collection.delete_collection(
                name=self.collection_name
            )
        except Exception:
            pass

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Evidence chunks for case-specific retrieval"
                }
            )
        )