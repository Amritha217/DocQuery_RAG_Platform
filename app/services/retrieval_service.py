import os
import json
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from app.services.embedding_service import generate_embeddings, generate_single_embedding

VECTOR_STORE_DIR = "vector_store"
cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def _get_paths(document_id: int):
    doc_folder = os.path.join(VECTOR_STORE_DIR, str(document_id))
    os.makedirs(doc_folder, exist_ok=True)
    return os.path.join(doc_folder, "index.faiss"), os.path.join(doc_folder, "chunks.json")


def create_faiss_index(document_id: int, chunks: list[dict]):
    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)
    embeddings_np = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_np)

    index_path, chunks_path = _get_paths(document_id)
    faiss.write_index(index, index_path)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)


def search_faiss(document_id: int, query: str, top_k: int = 5) -> list[dict]:
    index_path, chunks_path = _get_paths(document_id)
    if not os.path.exists(index_path):
        return []

    index = faiss.read_index(index_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    query_embedding = generate_single_embedding(query)
    query_np = np.array([query_embedding]).astype("float32")
    faiss.normalize_L2(query_np)

    scores, indices = index.search(query_np, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append({"chunk": chunks[idx]["text"], "page": chunks[idx]["page"], "score": float(score)})
    return results


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def create_bm25_index(document_id: int, chunks: list[dict]):
    doc_folder = os.path.join(VECTOR_STORE_DIR, str(document_id))
    os.makedirs(doc_folder, exist_ok=True)
    bm25_chunks_path = os.path.join(doc_folder, "bm25_chunks.json")
    with open(bm25_chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)


def search_bm25(document_id: int, query: str, top_k: int = 5) -> list[dict]:
    doc_folder = os.path.join(VECTOR_STORE_DIR, str(document_id))
    bm25_chunks_path = os.path.join(doc_folder, "bm25_chunks.json")
    if not os.path.exists(bm25_chunks_path):
        return []

    with open(bm25_chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    tokenized_chunks = [_tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    scores = bm25.get_scores(_tokenize(query))
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({"chunk": chunks[idx]["text"], "page": chunks[idx]["page"], "score": float(scores[idx])})
    return results


def _normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return results
    scores = [r["score"] for r in results]
    min_score, max_score = min(scores), max(scores)
    if max_score == min_score:
        for r in results:
            r["normalized_score"] = 1.0
        return results
    for r in results:
        r["normalized_score"] = (r["score"] - min_score) / (max_score - min_score)
    return results


def hybrid_search(document_id: int, query: str, top_k: int = 5, faiss_weight: float = 0.5) -> list[dict]:
    faiss_results = _normalize_scores(search_faiss(document_id, query, top_k=top_k * 2))
    bm25_results = _normalize_scores(search_bm25(document_id, query, top_k=top_k * 2))

    combined = {}
    for r in faiss_results:
        combined[r["chunk"]] = {"chunk": r["chunk"], "page": r["page"], "faiss_score": r["normalized_score"], "bm25_score": 0.0}
    for r in bm25_results:
        if r["chunk"] in combined:
            combined[r["chunk"]]["bm25_score"] = r["normalized_score"]
        else:
            combined[r["chunk"]] = {"chunk": r["chunk"], "page": r["page"], "faiss_score": 0.0, "bm25_score": r["normalized_score"]}

    final_results = []
    for data in combined.values():
        score = (faiss_weight * data["faiss_score"]) + ((1 - faiss_weight) * data["bm25_score"])
        final_results.append({"chunk": data["chunk"], "page": data["page"], "score": score})

    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:top_k]


def rerank_results(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    if not results:
        return results
    pairs = [[query, r["chunk"]] for r in results]
    scores = cross_encoder_model.predict(pairs)
    for i, r in enumerate(results):
        r["rerank_score"] = float(scores[i])
    results.sort(key=lambda x: x["rerank_score"], reverse=True)
    return results[:top_k]