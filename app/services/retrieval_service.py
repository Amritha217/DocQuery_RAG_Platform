# handles the retrieval and reranking stages

import json
import os
import re
import shutil
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.services.embedding_service import (
    generate_embeddings,
    generate_single_embedding,
)

VECTOR_STORE_DIR = "vector_store"

# Model used to rerank retrieved chunks
# cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# To keep tests fast and avoid downloading the model in CI , give it as None. Load it only when needed
# initialize the model only when reranking is actually requested

cross_encoder = None


# 1. Get the file paths to store or load a document's FAISS index and chunks

# - Creates a folder for the document inside vector_store/
# - Defines the path for index.faiss, which stores the FAISS index
# - Defines the path for chunks.json, which stores the original chunks and their metadata.
# - Returns both file paths


# Adjusting the document paths in vectore store to store each uploaded files bm25 ,faiss chunks
# Stores them as vector_store/intor_to_ml.pdf/1/bm25_chunks.json (or chunks.json , index.faiss)

def get_document_paths(storage_key: str):
    document_folder = os.path.join(
        VECTOR_STORE_DIR, storage_key
    )
    os.makedirs(document_folder, exist_ok=True)

    faiss_index_path = os.path.join(
        document_folder, "index.faiss"
    )
    chunks_path = os.path.join(
        document_folder, "chunks.json"
    )
    bm25_chunks_path = os.path.join(
        document_folder, "bm25_chunks.json"
    )

    return faiss_index_path, chunks_path, bm25_chunks_path


def delete_document_index(storage_key: str):
    document_folder = os.path.join(
        VECTOR_STORE_DIR, storage_key
    )

    if os.path.exists(document_folder):
        shutil.rmtree(document_folder)


# 2. Convert document chunks into embeddings and save a FAISS index for similarity search.

# - Extracts the text from every chunk
# - Generates an embedding vector for each chunk using generate_embeddings()
# - Converts the embeddings into NumPy float32 arrays, which FAISS expects
# - Normalizes the vectors so their lengths are 1
# - Creates a FAISS index using inner-product similarity
# - Adds the embedding vectors to the index
# - Saves the FAISS index to index.faiss
# - Saves the original chunks to chunks.json so search results can be mapped back to their text and page information


def create_faiss_index(storage_key: str, chunks: list[dict]):
    chunk_texts = [chunk["text"] for chunk in chunks]

    embeddings = np.array(
        generate_embeddings(chunk_texts), dtype="float32"
    )
    faiss.normalize_L2(embeddings)

    vector_dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(vector_dimension)
    faiss_index.add(embeddings)

    faiss_index_path, chunks_path, _ = get_document_paths(storage_key)

    faiss.write_index(faiss_index, faiss_index_path)

    with open(chunks_path, "w", encoding="utf-8") as file:
        json.dump(chunks, file)

# 3. Find document chunks whose meanings are similar to the user's question

# - Gets the paths for the FAISS index and stored chunks
# - Checks whether the FAISS index exists; if not, returns an empty list
# - Loads the index and chunks from disk
# - Generates an embedding for the user's question
# - Normalizes the question embedding
# - Searches the FAISS index for the top_k most similar chunks
# - Collects each result's text, page number, and similarity score
# - Returns the matching chunks, with the highest similarity scores first
        

def search_faiss(
    storage_key: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    faiss_index_path, chunks_path, _ = get_document_paths(storage_key)

    if not os.path.exists(faiss_index_path):
        return []

    faiss_index = faiss.read_index(faiss_index_path)

    with open(chunks_path, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    query_embedding = np.array(
        [generate_single_embedding(query)], dtype="float32"
    )
    faiss.normalize_L2(query_embedding)

    similarity_scores, chunk_indices = faiss_index.search(
        query_embedding, top_k
    )

    results = []

    for score, chunk_index in zip(
        similarity_scores[0], chunk_indices[0]
    ):
        if chunk_index == -1:
            continue

        results.append({
            "chunk": chunks[chunk_index]["text"],
            "page": chunks[chunk_index]["page"],
            "score": float(score),
        })

    return results

# 4. Prepare text for BM25 keyword search

# - Converts the text to lowercase
# - Splits the text into words using whitespace
# - Returns the list of words


def tokenize_text(text: str) -> list[str]:
    return text.lower().split()


# 5. Save document chunks so they can be used for BM25 keyword search 

# - Creates the document's storage folder if needed
# - Defines the path for bm25_chunks.json
# - Saves all the chunks to that JSON file

def create_bm25_index(storage_key: str, chunks: list[dict]):
    _, _, bm25_chunks_path = get_document_paths(storage_key)

    with open(bm25_chunks_path, "w", encoding="utf-8") as file:
        json.dump(chunks, file)


# 6. Find document chunks that match the words in the user's question

# - Locates and loads the stored chunks
# - Returns an empty list if the BM25 chunks file does not exist
# - Tokenizes every chunk's text
# - Builds a BM25 index from those tokenized chunks.
# - Tokenizes the user's question
# - Calculates a relevance score for each chunk based on keyword matches
# - Selects the top-ranked chunks and excludes chunks with scores of zero or less
# - Returns the matching chunk text, page number, and BM25 score


def search_bm25(
    storage_key: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    _, _, bm25_chunks_path = get_document_paths(storage_key)

    if not os.path.exists(bm25_chunks_path):
        return []

    with open(bm25_chunks_path, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    tokenized_chunks = [
        tokenize_text(chunk["text"]) for chunk in chunks
    ]

    bm25_index = BM25Okapi(tokenized_chunks)
    keyword_scores = bm25_index.get_scores(tokenize_text(query))
    ranked_indices = np.argsort(keyword_scores)[::-1][:top_k]

    results = []

    for chunk_index in ranked_indices:
        if keyword_scores[chunk_index] > 0:
            results.append({
                "chunk": chunks[chunk_index]["text"],
                "page": chunks[chunk_index]["page"],
                "score": float(keyword_scores[chunk_index]),
            })

    return results


# 7. Convert search scores to a common scale between 0 and 1

# - Returns the original empty list if there are no results
# - Finds the lowest and highest scores in the result list
# - If all scores are equal, assigns every result a normalized score of 1.0
# - Otherwise, scales each score between 0 and 1
# - Returns the results with an additional normalized_score field
# This helps combine FAISS and BM25 scores, because their original score ranges can differ


def normalize_scores(search_results: list[dict]) -> list[dict]:
    if not search_results:
        return search_results

    scores = [result["score"] for result in search_results]
    lowest_score = min(scores)
    highest_score = max(scores)

    if highest_score == lowest_score:
        for result in search_results:
            result["normalized_score"] = 1.0

        return search_results

    for result in search_results:
        result["normalized_score"] = (
            (result["score"] - lowest_score)
            / (highest_score - lowest_score)
        )

    return search_results


# 8. Combine FAISS similarity search and BM25 keyword search into one ranked list

# - Searches with FAISS and retrieves up to top_k * 2 candidates
# - Searches with BM25 and retrieves up to top_k * 2 candidates
# - Normalizes the scores from each search method separately
# - Combines the results, matching identical chunks by their exact text
# - Gives each chunk a FAISS score and a BM25 score. If a chunk appears in only one search, its other score is set to zero
# - Calculates a combined score using faiss_weight
# - Sorts all combined results from highest to lowest score
# - Returns the best top_k chunks


def hybrid_search(
    document_id: int,
    query: str,
    top_k: int = 5,
    faiss_weight: float = 0.5,
) -> list[dict]:

    faiss_results = search_faiss(
        document_id, query, top_k=top_k * 2
    )
    bm25_results = search_bm25(
        document_id, query, top_k=top_k * 2
    )

    faiss_results = normalize_scores(faiss_results)
    bm25_results = normalize_scores(bm25_results)

    combined_results = {}

    # Add FAISS results
    for result in faiss_results:
        chunk_text = result["chunk"]

        combined_results[chunk_text] = {
            "chunk": chunk_text,
            "page": result["page"],
            "faiss_score": result["normalized_score"],
            "bm25_score": 0.0,
        }

    # Add BM25 scores or add chunks found only by BM25
    for result in bm25_results:
        chunk_text = result["chunk"]

        if chunk_text in combined_results:
            combined_results[chunk_text]["bm25_score"] = (
                result["normalized_score"]
            )
        else:
            combined_results[chunk_text] = {
                "chunk": chunk_text,
                "page": result["page"],
                "faiss_score": 0.0,
                "bm25_score": result["normalized_score"],
            }

    # Calculate a combined score for each chunk
    final_results = []

    for result in combined_results.values():
        combined_score = (
            faiss_weight * result["faiss_score"]
            + (1 - faiss_weight) * result["bm25_score"]
        )

        final_results.append({
            "chunk": result["chunk"],
            "page": result["page"],
            "score": combined_score,
        })

    final_results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    return final_results[:top_k]


# 9. Reorder retrieved chunks based on how relevant they are to the user's question, using a cross-encoder model

# - Returns an empty list if there are no search results
# - Creates pairs containing the question and each retrieved chunk
# - Passes those pairs to the cross-encoder model
# - Gets a reranking score for each question–chunk pair
# - Adds each score to its corresponding result as rerank_score
# - Sorts the chunks by reranking score, from highest to lowest
# - Returns the top top_k chunks

def rerank_results(
    query: str,
    search_results: list[dict],
    top_k: int = 5,
) -> list[dict]:
    global cross_encoder

    if not search_results:
        return []

    if cross_encoder is None:
        cross_encoder = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    question_chunk_pairs = [
        [query, result["chunk"]]
        for result in search_results
    ]

    reranking_scores = cross_encoder.predict(question_chunk_pairs)

    reranked_results = []

    for index, result in enumerate(search_results):
        updated_result = result.copy()
        updated_result["rerank_score"] = float(
            reranking_scores[index]
        )
        reranked_results.append(updated_result)

    reranked_results.sort(
        key=lambda result: result["rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]




def create_storage_key(filename: str) -> str:
    # Get the filename without its extension
    document_name = Path(filename).stem

    # Make the folder name safe
    document_name = re.sub(
        r"[^a-zA-Z0-9_-]+", "_", document_name
    ).strip("_")

    if not document_name:
        document_name = "document"

    document_folder = os.path.join(
        VECTOR_STORE_DIR, document_name
    )
    os.makedirs(document_folder, exist_ok=True)

    # Find the lowest available number
    folder_number = 1

    while os.path.exists(
        os.path.join(document_folder, str(folder_number))
    ):
        folder_number += 1

    return os.path.join(document_name, str(folder_number))


