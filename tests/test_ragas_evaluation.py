import json

from eval import ragas_evaluation as ragas_eval


def test_is_abstention_detects_expected_message():
    answer = ragas_eval.ABSTENTION_MESSAGE

    assert ragas_eval.is_abstention(answer) is True


def test_is_abstention_is_case_insensitive():
    answer = ragas_eval.ABSTENTION_MESSAGE.upper()

    assert ragas_eval.is_abstention(answer) is True


def test_is_abstention_returns_false_for_normal_answer():
    assert ragas_eval.is_abstention(
        "The document explains machine learning."
    ) is False


def test_load_dataset_reads_json_file(tmp_path, monkeypatch):
    dataset = [
        {
            "id": 1,
            "question": "What is machine learning?",
            "answerable": True,
            "reference_answer": "A field of AI.",
        }
    ]

    dataset_path = tmp_path / "golden_dataset.json"
    dataset_path.write_text(
        json.dumps(dataset),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        ragas_eval,
        "DATASET_PATH",
        dataset_path,
    )

    assert ragas_eval.load_dataset() == dataset


def test_retrieve_context_uses_hybrid_search_and_reranking(
    monkeypatch,
):
    candidates = [
        {"chunk": "Candidate passage", "score": 0.9}
    ]
    reranked = [
        {"chunk": "Best passage", "score": 0.95}
    ]

    def fake_hybrid_search(document_id, question, top_k):
        assert document_id == 7
        assert question == "What is AI?"
        assert top_k == 10
        return candidates

    def fake_rerank_results(question, results, top_k):
        assert question == "What is AI?"
        assert results == candidates
        assert top_k == 5
        return reranked

    monkeypatch.setattr(
        ragas_eval,
        "hybrid_search",
        fake_hybrid_search,
    )
    monkeypatch.setattr(
        ragas_eval,
        "rerank_results",
        fake_rerank_results,
    )

    result = ragas_eval.retrieve_context(7, "What is AI?")

    assert result == reranked