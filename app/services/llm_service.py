from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = ""
    for chunk in chunks:
        context += f"{chunk['chunk']}\n\n"

    prompt = f"""You are a helpful tutor answering questions based ONLY on the provided context below.

Context:
{context}

Question: {question}

Instructions:
- Answer using ONLY the information in the context above.
- If the context does not contain enough information to answer the question, say "I don't have enough information in this document to answer that question."
- Be clear, concise, and write in a natural, conversational tone.

Answer:"""

    return prompt


def generate_answer(question: str, chunks: list[dict]) -> str:
    prompt = build_prompt(question, chunks)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )

    return response.choices[0].message.content