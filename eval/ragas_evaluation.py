# Evaluates how well the questions are being answered using the retrieved chunks

# Evaluating only for Hybrid search with reranking method

# Calculate the faithfulness , answer accuracy for each question in golden dataset against the retrieved chunks using ragas

import argparse
import asyncio
import json
from pathlib import Path

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerAccuracy, Faithfulness

from app.config import GROQ_API_KEY, GROQ_JUDGE_MODEL, GROQ_MODEL
from app.services.llm_service import generate_answer
from app.services.retrieval_service import hybrid_search, rerank_results

# Ouput of this file is stored as eval/ragas_results.json

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "eval" / "data" / "golden_dataset.json"
OUTPUT_PATH = ROOT_DIR / "eval" / "results" / "ragas_results.json"

ABSTENTION_MESSAGE = (
    "I don't have enough information in this document "
    "to answer that question."
)

# 1. Loads the golden dataset

def load_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


# 2. Retrieves relevant document chunks for a question.

# - Use hybrid search (FAISS + BM25) to retrieve the top 10
# - Apply reranking to select the top 5 most relevant chunks
    
def retrieve_context(document_id, question):
    candidates = hybrid_search(document_id, question, top_k=10)
    return rerank_results(question, candidates, top_k=5)


# 3. Check whether the generated answer contains the expected message

# - Takes the generated answer
# - Checks whether it contains the predefined abstention message, ignoring uppercase and lowercase differences.
# - Returns True if the message is found

def is_abstention(answer):
    return ABSTENTION_MESSAGE.lower() in answer.lower()

# 4. Runs the complete answer evaluation process.

async def main():
    parser = argparse.ArgumentParser()

    # - Accept the document ID and optional question limit
    
    parser.add_argument("--document-id", type=int, required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    # - Load the golden dataset

    dataset = load_dataset()

    if args.limit is not None:
        dataset = dataset[:args.limit]

    # - Sets up the judge model
        
    client = AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

    judge_llm = llm_factory(
        GROQ_JUDGE_MODEL or GROQ_MODEL,
        provider="openai",
        client=client,
        max_tokens=8192,
        temperature=0.0,
        reasoning_effort="low",
    )

    faithfulness_metric = Faithfulness(llm=judge_llm)
    accuracy_metric = AnswerAccuracy(llm=judge_llm)

    results = []

    # - Process each question in the dataset

    for item in dataset:
        question = item["question"]
        print(f"Evaluating: {question}")

        row = {
            "id": item["id"],
            "question": question,
            "answerable": item["answerable"],
            "generated_answer": "",
            "retrieved_context_count": 0,
            "faithfulness": None,
            "answer_accuracy": None,
            "abstention_correct": None,
            "error": None,
        }

        try:

            # - Retrieve relevant document chunks using hybrid search with reranking

            chunks = retrieve_context(args.document_id, question)
            contexts = [chunk["chunk"] for chunk in chunks]

            # - Generate an answer using the LLM,
            # or use the abstention message if no chunks are retrieved.

            answer = (
                generate_answer(question, chunks)
                if contexts
                else ABSTENTION_MESSAGE
            )

            row["generated_answer"] = answer
            row["retrieved_context_count"] = len(contexts)

            # - For answerable questions, 
            # calculate Faithfulness and Answer Accuracy using Ragas

            if item["answerable"]:
                faithfulness = await faithfulness_metric.ascore(
                    user_input=question,
                    response=answer,
                    retrieved_contexts=contexts,
                )

                accuracy = await accuracy_metric.ascore(
                    user_input=question,
                    response=answer,
                    reference=item["reference_answer"],
                )

                row["faithfulness"] = float(faithfulness.value)
                row["answer_accuracy"] = float(accuracy.value)

            # - For unanswerable questions, check whether the chatbot correctly abstains
                
            else:
                row["abstention_correct"] = is_abstention(answer)

        except (ValueError, TypeError) as exc:
            row["error"] = str(exc)
            print(f"Error: {exc}")

        results.append(row)

        # - Save progress after each question.
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT_PATH.open("w", encoding="utf-8") as file:
            json.dump(results, file, indent=2, ensure_ascii=False)

        print(f"Faithfulness: {row['faithfulness']}")
        print(f"Answer accuracy: {row['answer_accuracy']}")

    print(f"\nEvaluation complete. Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
