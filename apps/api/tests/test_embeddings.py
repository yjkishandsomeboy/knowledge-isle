from knowledge_isle_api.services.retrieval import _cosine_similarity


def test_cosine_similarity_handles_matching_and_zero_vectors() -> None:
    assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
