# Compares the 3 retriving methods - FAISS , Hybrid serach (BM25 + FAISS) , Hybrid Search with reranking
# compare three ways of retrieving relevant text chunks & determines which approach works well
# We calculate - Recall@ , MRR , nDCG using the 3 methods for each qns in golden dataset
# Result stored in retrieval_report.json


import argparse
import json
import math
from pathlib import Path

from app.services.retrieval_service import (
    search_faiss,
    hybrid_search,
    rerank_results,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "eval" / "data" / "golden_dataset.json"
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"

TOP_K = 5


# This function makes text comparison more reliable by -
# converting all letters to lowercase , removing leading & trailing whitespace , converting extra spaces , tabs , newlines into single space.

def normalize_text(text: str) -> str:
    """Normalize whitespace and case for exact chunk matching."""
    return " ".join(text.lower().split())

# opens golden_dataset.json, reads the JSON, and converts it into Python objects

def load_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)

# builds the path to the selected document's chunk file
# for intro_to_ml.pdf the chunks lie in the below mentioned folder
    
def load_indexed_chunks(document_id: int):
    chunks_path = (
        VECTOR_STORE_DIR / str(document_id) / "chunks.json"
    )

    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Missing chunk file: {chunks_path}. "
            "Upload and index the document first."
        )

    # loads the indexed chunk records into memory

    with chunks_path.open("r", encoding="utf-8") as file:
        return json.load(file)

# This function checks whether every passage marked as relevant (relevant_passages) within golden_dataset.json actually exists among the indexed chunks (chunks from intro_to_ml.pdf).
    
def validate_relevance_labels(dataset, indexed_chunks):
    """Ensure every labeled relevant passage exists in the index."""
    corpus = {
        normalize_text(chunk["text"])
        for chunk in indexed_chunks
    }

    for item in dataset:
        for passage in item["relevant_passages"]:
            if normalize_text(passage) not in corpus:
                raise ValueError(
                    f"Question {item['id']}: a relevant passage "
                    "does not match any indexed chunk. Copy the "
                    "exact chunk text from chunks.json."
                )

# recall_at_k() — measuring how many relevant chunks were found
            
def recall_at_k(retrieved, relevant, k):

    # relevant chunks - ground truth from your golden dataset
    relevant_set = set(relevant)

    # If a qns doesn't have relevant chunks recall cannot be calculated . So return None

    if not relevant_set:
        return None

    # Keep only the top k retrieved results.

    retrieved_set = {
        normalize_text(item["chunk"])
        for item in retrieved[:k]
    }

    # Calculate recall
    # & operator finds the intersection of the two sets: chunks that are both retrieved and labeled relevant.

    return len(retrieved_set & relevant_set) / len(relevant_set)

# reciprocal_rank() — measuring the first relevant result
# Function returns the result of the 5 chunks. If a relevant chunk is present at rank 1 , then its result is 1 , at rank 2 its result is 0.5 (1/2) and so on.

def reciprocal_rank(retrieved, relevant):
    relevant_set = set(relevant)

    for rank, item in enumerate(retrieved, start=1):
        if normalize_text(item["chunk"]) in relevant_set:
            return 1.0 / rank

    return 0.0

# ndcg_at_k() — measuring ranking quality

def ndcg_at_k(retrieved, relevant, k):
    relevant_set = set(relevant)

    if not relevant_set:
        return None

# Here a relevant chunk earns a score based on its rank
    
    dcg = 0.0

    for rank, item in enumerate(retrieved[:k], start=1):
        is_relevant = (
            normalize_text(item["chunk"]) in relevant_set
        )

        if is_relevant:
            dcg += 1.0 / math.log2(rank + 1)

# ideal DCG represents the best possible ordering: all available relevant chunks appear at the top.
# For example, if there are two relevant chunks and k=5, the ideal ranking puts them at ranks 1 and 2.

    ideal_relevant = min(len(relevant_set), k)

    ideal_dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant + 1)
    )

    # Dividing DCG by ideal DCG produces nDCG
    # if score = 1 , ranking is ideal for the labeled relevant chunks
    # A lower score means the relevant chunks are ranked less effectively

    return dcg / ideal_dcg if ideal_dcg else 0.0

# This function receives 2 inputs - golden_dataset & retrieve fn that retrieves chunks for a question

def evaluate_strategy(dataset, retrieve):
    per_question = []

    for item in dataset:
        # Retrieval metrics require at least one known relevant passage.
        relevant = [
            normalize_text(passage)
            for passage in item["relevant_passages"]
        ]

        if not item["answerable"] or not relevant:
            continue

        results = retrieve(item["question"])

        # Calculate the metrics (recall , mrr , ndcg) for each question and stores them along with the question ID.

        per_question.append({
            "id": item["id"],
            "recall_at_5": recall_at_k(
                results, relevant, TOP_K
            ),
            "mrr": reciprocal_rank(results, relevant),
            "ndcg_at_5": ndcg_at_k(
                results, relevant, TOP_K
            ),
        })

    if not per_question:
        raise ValueError(
            "No answerable questions with relevant passages "
            "were available for evaluation."
        )

    summary = {}

    for metric in ("recall_at_5", "mrr", "ndcg_at_5"):
        summary[metric] = sum(
            row[metric] for row in per_question
        ) / len(per_question)

    summary["evaluated_questions"] = len(per_question)
    summary["per_question"] = per_question

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark DocQuery retrieval strategies."
    )

    parser.add_argument(
        "--document-id",
        type=int,
        required=True,
        help="ID of the indexed document to evaluate.",
    )

    args = parser.parse_args()

    dataset = load_dataset()
    indexed_chunks = load_indexed_chunks(args.document_id)

    validate_relevance_labels(dataset, indexed_chunks)



    # Define the three retrieval strategies
    
    strategies = {
        "faiss_only": lambda question: search_faiss(
            args.document_id, question, top_k=TOP_K
        ),
        "hybrid": lambda question: hybrid_search(
            args.document_id, question, top_k=TOP_K
        ),
        "hybrid_reranked": lambda question: rerank_results(
            question,
            hybrid_search(
                args.document_id, question, top_k=10
            ),
            top_k=TOP_K,
        ),
    }

    report = {}

    for name, retrieve in strategies.items():
        print(f"Evaluating: {name}")

        report[name] = evaluate_strategy(dataset, retrieve)

        summary = report[name]

        print(
            f"Recall@5: {summary['recall_at_5']:.3f} | "
            f"MRR: {summary['mrr']:.3f} | "
            f"nDCG@5: {summary['ndcg_at_5']:.3f}"
        )

    output_dir = ROOT_DIR / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "retrieval_report.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
