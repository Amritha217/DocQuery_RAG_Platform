# Purpose: Uses a sentence-transformer model (all-MiniLM-L6-v2) to convert text into a numeric vector (embedding) that captures semantic meaning.

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


# 1. Convert the document text to embeddings

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


# 2. Converts user qns to embedding

def generate_single_embedding(text: str) -> list[float]:
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()