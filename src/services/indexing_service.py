from src.loaders.dataset_loader import (
    VendorVerdictDataset
)

from src.rag.embedder import OpenAIEmbedder

from src.rag.vector_store import ChromaVectorStore

from src.services.chunking_service import ChunkingService

class IndexingService:

    def __init__(
            self,
            dataset: VendorVerdictDataset,
            embedder: OpenAIEmbedder,
            vector_store: ChromaVectorStore,
            chunking_service: ChunkingService,
            batch_size: int = 100
    ):
        self.dataset = dataset
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunking_service = chunking_service
        self.batch_size = batch_size


    def index_case(
            self,
            case_id: str
    ) -> dict:
        chunks = (
            self.chunking_service
            .build_case_chunks(
                case_id
            )
        )

        if not chunks:
            return {"case_id": case_id, "chunks": 0, "status": "no_usable_evidence"}

        self.vector_store.delete_case(case_id)

        indexed = 0

        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start:start + self.batch_size]
            texts = [chunk.text for chunk in batch]

            embeddings = self.embedder.embed_batch(texts)

            self.vector_store.add_chunks(
                chunks=batch,
                embeddings=embeddings
            )

            indexed += len(batch)

        return {"case_id": case_id, "chunks": indexed, "status": "indexed"}



    def index_all(self) -> dict:
        case_ids = self.dataset.cases_df["case_id"].tolist()
        total_index = 0
        case_results = []

        for case_id in case_ids:
            result = self.index_case(case_id)
            case_results.append(result)
            total_index += result["chunks"]

        return {"cases": case_results, "chunks": total_index, "collection_count": self.vector_store.collection.count(),
                "results": case_results}