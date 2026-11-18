from src.rag.embedder import OpenAIEmbedder
from src.rag.vector_store import ChromaVectorStore

class EvidenceRetriever:
    def __init__(
            self,
            embedder: OpenAIEmbedder,
            vector_store: ChromaVectorStore
    ):
        self.embedder = embedder
        self.vector_store = vector_store


    def search(
            self,
            case_id: str,
            query: str,
            top_k: int = 5
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Query must not be empty.")

        
        query_embedding = self.embedder.embed_batch([query])[0]
        results = self.vector_store.query(
            query_embedding=query_embedding,
            case_id=case_id,
            n_results=top_k
        )

        return self._normalize_results(results)


    def _normalize_results(self, results: dict) -> list[dict]:
        if not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        normalized = []

        for index, chunk_id in enumerate(ids):
            normalized.append(
                {
                    "chunk_id": chunk_id,
                    "text": documents[index],
                    "metadata": metadatas[index],
                    "distance": distances[index]
                }
            )

        return normalized