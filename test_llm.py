from app.services.pdf_service import extract_text, chunk_text
from app.services.retrieval_service import create_faiss_index, create_bm25_index, hybrid_search, rerank_results
from app.services.llm_service import generate_answer

file_path = "uploads/1/dsa.pdf"  # use a real uploaded file
document_id = 999

text = extract_text(file_path)
chunks = chunk_text(text)

create_faiss_index(document_id, chunks)
create_bm25_index(document_id, chunks)
print("Indexes created!")

query = "What is linear data structure?"  # ask a real question about your document

hybrid_results = hybrid_search(document_id, query, top_k=10)
final_chunks = rerank_results(query, hybrid_results, top_k=3)

print(f"\nGenerating answer using {len(final_chunks)} chunks...\n")

answer = generate_answer(query, final_chunks)

print("--- ANSWER ---")
print(answer)