"""
knowledge_base.py — Vector search over FAQs and policy documents.

Uses sentence-transformers to convert text to embeddings (numbers that
capture meaning), then ChromaDB to store and search those embeddings.

This allows the agent to find relevant answers even when the caller's
exact words don't match the FAQ — it searches by MEANING, not keywords.

Functions:
  add_documents(docs) → load FAQ/policy text into the vector DB
  search(query, n)    → find the top-n most relevant FAQ entries
"""

import chromadb
from sentence_transformers import SentenceTransformer

# Load a lightweight embedding model (runs locally, no API key needed)
# all-MiniLM-L6-v2 is fast and accurate for FAQ-style search
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create in-memory ChromaDB client
chroma = chromadb.Client()

# Get or create a collection called "faq" to store our documents
try:
    collection = chroma.get_collection("faq")
except Exception:
    collection = chroma.create_collection("faq")


def add_documents(docs: list):
    """
    Load FAQ documents into the vector database.

    Each doc should be: {"id": "1", "text": "...", "metadata": {...}}
    The text is converted to an embedding vector and stored.

    Call this once via seed_knowledge.py before launching the app.
    """
    texts      = [d["text"]             for d in docs]
    ids        = [d["id"]               for d in docs]
    metadatas  = [d.get("metadata", {}) for d in docs]
    embeddings = model.encode(texts).tolist()

    collection.add(
        documents=texts,
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print(f"Added {len(docs)} documents to knowledge base.")


def search(query: str, n: int = 3) -> str:
    """
    Search the knowledge base using the caller's question.

    Steps:
      1. Convert query to an embedding vector
      2. ChromaDB finds the n closest matching documents
      3. Return them joined as a string for Groq to read

    Example:
      search("how do I pay my bill?")
      → returns FAQ text about billing and payment methods
    """
    embedding = model.encode([query]).tolist()
    results   = collection.query(query_embeddings=embedding, n_results=n)
    docs      = results.get("documents", [[]])[0]

    if not docs:
        return "No relevant information found in knowledge base."

    return "\n---\n".join(docs)
