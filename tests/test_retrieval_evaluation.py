import pytest

from eval.retrieval_evaluation import (
    evaluate_strategy,
    ndcg_at_k,
    normalize_text,
    recall_at_k,
    reciprocal_rank,
    validate_relevance_labels,
)


def test_normalize_text():
    assert normalize_text("  Hello   WORLD\n") == "hello world"


def test_recall_at_k():
    retrieved = [
        {"chunk": "Relevant passage A"},
        {"chunk": "Irrelevant passage"},
    ]
    relevant = ["relevant passage a", "relevant passage b"]

    assert recall_at_k(retrieved, relevant, 5) == 0.5


def test_recall_at_k_returns_none_without_relevant_passages():
    assert recall_at_k([], [], 5) is None


def test_reciprocal_rank():
    retrieved = [
        {"chunk": "Irrelevant passage"},
        {"chunk": "Relevant passage"},
    ]

    assert reciprocal_rank(retrieved, ["relevant passage"]) == 0.5


def test_reciprocal_rank_returns_zero_when_no_match():
    retrieved = [{"chunk": "Unrelated content"}]

    assert reciprocal_rank(retrieved, ["relevant passage"]) == 0.0


def test_ndcg_at_k():
    retrieved = [
        {"chunk": "Relevant passage"},
        {"chunk": "Irrelevant passage"},
    ]

    assert ndcg_at_k(retrieved, ["relevant passage"], 5) == pytest.approx(1.0)


def test_ndcg_at_k_returns_none_without_relevant_passages():
    assert ndcg_at_k([], [], 5) is None


def test_validate_relevance_labels_accepts_matching_chunks():
    dataset = [
        {
            "id": 1,
            "relevant_passages": ["Relevant passage"],
        }
    ]
    indexed_chunks = [{"text": "  RELEVANT   passage "}]

    # Should not raise an exception.
    validate_relevance_labels(dataset, indexed_chunks)


def test_validate_relevance_labels_rejects_missing_chunk():
    dataset = [
        {
            "id": 1,
            "relevant_passages": ["Missing passage"],
        }
    ]
    indexed_chunks = [{"text": "Some other content"}]

    with pytest.raises(ValueError, match="Question 1"):
        validate_relevance_labels(dataset, indexed_chunks)


def test_evaluate_strategy_calculates_average_metrics():
    dataset = [
        {
            "id": 1,
            "question": "Question A?",
            "answerable": True,
            "relevant_passages": ["Passage A"],
        },
        {
            "id": 2,
            "question": "Question B?",
            "answerable": True,
            "relevant_passages": ["Passage B"],
        },
        {
            "id": 3,
            "question": "Unanswerable question?",
            "answerable": False,
            "relevant_passages": [],
        },
    ]

    def fake_retrieve(question):
        if question == "Question A?":
            return [{"chunk": "Passage A"}]
        return [{"chunk": "Unrelated content"}]

    summary = evaluate_strategy(dataset, fake_retrieve)

    assert summary["evaluated_questions"] == 2
    assert summary["recall_at_5"] == pytest.approx(0.5)
    assert summary["mrr"] == pytest.approx(0.5)
    assert summary["ndcg_at_5"] == pytest.approx(0.5)
    assert len(summary["per_question"]) == 2


def test_evaluate_strategy_raises_without_evaluable_questions():
    dataset = [
        {
            "id": 1,
            "question": "Unanswerable question?",
            "answerable": False,
            "relevant_passages": [],
        }
    ]

    with pytest.raises(ValueError, match="No answerable questions"):
        evaluate_strategy(dataset, lambda question: [])