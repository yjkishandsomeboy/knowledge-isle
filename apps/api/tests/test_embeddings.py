from knowledge_isle_api.services.embeddings import embedding_is_configured


def test_embeddings_are_disabled_without_explicit_configuration() -> None:
    assert embedding_is_configured() is False
