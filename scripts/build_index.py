from src.loaders.dataset_loader import VendorVerdictDataset

from src.rag.embedder import OpenAIEmbedder

from src.rag.vector_store import ChromaVectorStore

from src.services.validation_service import ValidationService

from src.services.chunking_service import ChunkingService

from src.services.indexing_service import IndexingService

def main():
    dataset = VendorVerdictDataset().load()
    validation_service = ValidationService(dataset)
    chunking_service = ChunkingService(
        dataset=dataset,
        validation_service=validation_service
    )

    embedder = OpenAIEmbedder()

    vector_store = ChromaVectorStore()

    indexing_service = IndexingService(
        dataset=dataset,
        chunking_service=chunking_service,
        embedder=embedder,
        vector_store=vector_store,
        batch_size=100
    )

    result = indexing_service.index_all()

    print()

    print("="*60)
    print("Vendor Verdict Vector index")
    print("="*60)
    print("Cases indexed:", result["cases"])
    print("Chunks indexed:", result["chunks"])
    print("Collection Count:", result["collection_count"])
    

if __name__ == "__main__":
    main()