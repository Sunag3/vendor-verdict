from src.rag.embedder import OpenAIEmbedder
from src.rag.vector_store import ChromaVectorStore
from src.rag.retriever import EvidenceRetriever

CASE_ID = "c0001"

embedder = OpenAIEmbedder()

vector_store = ChromaVectorStore()

retriever = EvidenceRetriever(
    embedder=embedder,
    vector_store=vector_store
)


results = retriever.search(
    case_id=CASE_ID,
    query= (
        #"SSO SAML single sign-on",
        "uptime for the previous 90 days"
    ),
    top_k=5
)

for result in results:
    print()
    print(
        "chunk", result['chunk_id']
    )

    print("Distance:", result['distance'])

    print("Page:", result['metadata']['page_id'])

    print(result['text'][:500])

    print("="*60)

