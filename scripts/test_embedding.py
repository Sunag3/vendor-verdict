from src.rag.embedder import OpenAIEmbedder

def main():
    embedder = OpenAIEmbedder()

    vector = embedder.embed_text(
        "SAML SSO is available."
        "on paid plans"
    )

    print(
        "Embedding dimensions:",
        len(vector)
    )

    print(
        "First 5 values:",
        vector[:5]
    )


if __name__ == "__main__":
    main()