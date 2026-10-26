# LLM generates a ans based on the user qns and retrieved relevant chunks

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

# 1. Prepare the prompt that tells the LLM how to answer the user's question using the retrieved document chunks.

# - Receives  user's question and  relevant chunks retrieved by the RAG pipelin
# - Combines the text from all the chunks into a single context
# - Adds the user's question to the prompt
# - Provides instructions to answer only using the given context
# - Returns the completed prompt as a string

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

# 2. Send the question and retrieved context to the Groq-hosted LLM and generate an answer.

# - Calls build_prompt() to prepare the prompt
# - Sends the prompt to the LLM using the Groq API
# - Specifies the model , temperature , tokens (to limit the length of generated response)
# - Extracts and returns the generated answer text from the API respons

def generate_answer(question: str, chunks: list[dict]) -> str:
    prompt = build_prompt(question, chunks)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )

    return response.choices[0].message.content