
import numpy as np
import pytest

from app.services import retrieval_service as retrieval


@pytest.fixture
def isolated_vector_store(tmp_path, monkeypatch):
    """Use a temporary vector store for each test."""
    monkeypatch.setattr(
        retrieval, "VECTOR_STORE_DIR", str(tmp_path)
    )
    return tmp_path


def fake_embeddings(texts):
    """Generate simple, predictable vectors for testing."""
    vectors = []

    for text in texts:
        if "biology" in text.lower():
            vectors.append([1.0, 0.0])
        else:
            vectors.append([0.0, 1.0])

    return vectors


def fake_single_embedding(text):
    if "biology" in text.lower():
        return [1.0, 0.0]

    return [0.0, 1.0]


def test_search_faiss_returns_relevant_chunk(
    isolated_vector_store, monkeypatch
):
    monkeypatch.setattr(
        retrieval, "generate_embeddings", fake_embeddings
    )
    monkeypatch.setattr(
        retrieval,
        "generate_single_embedding",
        fake_single_embedding,
    )

    chunks = [
        {"text": "Biology studies living organisms.", "page": 1},
        {"text": "History studies past events.", "page": 2},
    ]

    retrieval.create_faiss_index("Biology/1", chunks)

    results = retrieval.search_faiss(
        "Biology/1", "biology", top_k=2
    )

    assert len(results) == 2
    assert results[0]["chunk"] == chunks[0]["text"]
    assert results[0]["page"] == 1
    assert isinstance(results[0]["score"], float)


def test_search_faiss_returns_empty_when_index_missing(
    isolated_vector_store,
):
    results = retrieval.search_faiss(
        "Missing/1", "biology"
    )

    assert results == []


def test_search_bm25_returns_keyword_match(
    isolated_vector_store,
):
    chunks = [
        {
            "text": "Mitochondria produce energy inside cells.",
            "page": 1,
        },
        {
            "text": "Photosynthesis occurs in chloroplasts.",
            "page": 2,
        },
        {
            "text": "Gravity affects the motion of objects.",
            "page": 3,
        },
    ]

    retrieval.create_bm25_index("Biology/1", chunks)

    results = retrieval.search_bm25(
        "Biology/1", "mitochondria energy", top_k=3
    )

    assert results
    assert results[0]["chunk"] == chunks[0]["text"]
    assert results[0]["page"] == 1


def test_search_bm25_returns_empty_when_index_missing(
    isolated_vector_store,
):
    results = retrieval.search_bm25(
        "Missing/1", "mitochondria"
    )

    assert results == []


def test_normalize_scores():
    results = [
        {"chunk": "A", "page": 1, "score": 2.0},
        {"chunk": "B", "page": 2, "score": 4.0},
        {"chunk": "C", "page": 3, "score": 6.0},
    ]

    normalized = retrieval.normalize_scores(results)

    assert [
        item["normalized_score"] for item in normalized
    ] == pytest.approx([0.0, 0.5, 1.0])


def test_normalize_scores_handles_equal_scores():
    results = [
        {"chunk": "A", "page": 1, "score": 3.0},
        {"chunk": "B", "page": 2, "score": 3.0},
    ]

    normalized = retrieval.normalize_scores(results)

    assert [
        item["normalized_score"] for item in normalized
    ] == [1.0, 1.0]


def test_hybrid_search_combines_results(monkeypatch):
    faiss_results = [
        {"chunk": "Biology chunk", "page": 1, "score": 0.9},
        {"chunk": "FAISS-only chunk", "page": 2, "score": 0.5},
    ]

    bm25_results = [
        {"chunk": "Biology chunk", "page": 1, "score": 8.0},
        {"chunk": "BM25-only chunk", "page": 3, "score": 4.0},
    ]

    monkeypatch.setattr(
        retrieval, "search_faiss",
        lambda *args, **kwargs: [item.copy() for item in faiss_results],
    )
    monkeypatch.setattr(
        retrieval, "search_bm25",
        lambda *args, **kwargs: [item.copy() for item in bm25_results],
    )

    results = retrieval.hybrid_search(
        "Biology/1", "biology", top_k=3, faiss_weight=0.5
    )

    assert len(results) == 3
    assert results[0]["chunk"] == "Biology chunk"
    assert results[0]["score"] == pytest.approx(1.0)

    returned_chunks = {item["chunk"] for item in results}
    assert "FAISS-only chunk" in returned_chunks
    assert "BM25-only chunk" in returned_chunks


def test_rerank_results_sorts_by_model_score(monkeypatch):
    class FakeCrossEncoder:
        def predict(self, pairs):
            return np.array([0.2, 0.9, 0.5])

    monkeypatch.setattr(
        retrieval, "cross_encoder", FakeCrossEncoder()
    )

    results = [
        {"chunk": "First chunk", "page": 1, "score": 0.8},
        {"chunk": "Second chunk", "page": 2, "score": 0.7},
        {"chunk": "Third chunk", "page": 3, "score": 0.6},
    ]

    reranked = retrieval.rerank_results(
        "test question", results, top_k=2
    )

    assert len(reranked) == 2
    assert reranked[0]["chunk"] == "Second chunk"
    assert reranked[1]["chunk"] == "Third chunk"
    assert reranked[0]["rerank_score"] == pytest.approx(0.9)


def test_rerank_results_handles_empty_input():
    assert retrieval.rerank_results("question", []) == []
