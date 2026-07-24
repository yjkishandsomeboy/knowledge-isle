import httpx

from knowledge_isle_api.core.config import settings


async def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Request embeddings only when explicitly enabled; absent config keeps MVP behavior."""
    if not texts or not settings.ai_embeddings_enabled:
        return None
    if not settings.ai_base_url or not settings.ai_api_key:
        return None
    payload = {"model": settings.ai_embedding_model, "input": texts}
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post(
            f"{settings.ai_base_url.rstrip('/')}/embeddings", json=payload, headers=headers
        )
        response.raise_for_status()
    data = response.json().get("data", [])
    vectors = [item.get("embedding") for item in data if isinstance(item, dict)]
    if len(vectors) != len(texts) or not all(isinstance(vector, list) for vector in vectors):
        raise ValueError("Embedding provider returned an invalid vector batch")
    return [vector for vector in vectors if isinstance(vector, list)]


def embedding_is_configured() -> bool:
    return bool(settings.ai_embeddings_enabled and settings.ai_base_url and settings.ai_api_key)
