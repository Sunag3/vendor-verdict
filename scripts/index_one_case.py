from src.loaders.dataset_loader import VendorVerdictDataset
from src.rag.embedder import OpenAIEmbedder
from src.rag.vector_store import ChromaVectorStore
from src.services.validation_service import ValidationService
from src.services.chunking_service import ChunkingService
from src.services.indexing_service import IndexingService
from src.rag.vector_store import ChromaVectorStore

CASE_ID = "c0001"


dataset = VendorVerdictDataset().load()

validation_service = ValidationService(dataset)

chunking_service = ChunkingService(
    dataset=dataset,
    validation_service=validation_service
)

embedder = OpenAIEmbedder()

vector_store = ChromaVectorStore()

service = IndexingService(
    dataset=dataset,
    chunking_service=chunking_service,
    embedder=embedder,
    vector_store=vector_store
)

result = service.index_case(CASE_ID)


print(result)