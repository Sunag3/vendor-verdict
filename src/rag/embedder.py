from openai import OpenAI

from src.config.settings import settings


class OpenAIEmbedder:
    def __init__(
            self,
            model: str | None = None,
    ):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set to use OpenAIEmbedder.")

        
        self.model = model or settings.openai_embedding_model
        self.client = OpenAI(api_key=settings.openai_api_key)


    def embed_text(
            self,
            text: str,

    ) -> list[float]:
        if not text.strip():
            raise ValueError("Text must not be empty.")

        
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding


    def embed_batch(
            self,
            texts: list[str],

    ) -> list[list[float]]:
        if not texts:
            raise ValueError("Texts must not be empty.")
        if any(not text.strip() for text in texts):
            raise ValueError("Texts must not contain empty strings.")


        cleaned = [
            text
            for text in texts
            if text.strip()
        ]

        if len(cleaned) != len(texts):
            raise ValueError("Texts must not contain empty strings.")

        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned,
        )

        ordered = sorted(
            response.data,
            key=lambda item: item.index,
        )
        return [item.embedding for item in ordered]