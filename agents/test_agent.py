import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from openai import OpenAI

# 1. Initialize Qdrant Vector Memory Connection
qdrant_host = os.getenv("QDRANT_HOST", "127.0.0.1")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
qclient = QdrantClient(host=qdrant_host, port=qdrant_port)

collection_name = "shivanshos_memory"

# Ensure vector collection exists in Qdrant
collections = [col.name for col in qclient.get_collections().collections]
if collection_name not in collections:
    qclient.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    print(f"[Qdrant] Created Vector Collection: {collection_name}")
else:
    print(f"[Qdrant] Vector Collection '{collection_name}' is active.")

# 2. Query Ollama Local Agent Model (qwen2.5-coder:7b)
llm = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama")
)

response = llm.chat.completions.create(
    model=os.getenv("HERMES_MODEL", "qwen2.5-coder:7b"),
    messages=[
        {"role": "system", "content": "You are the core agent for GitHub org shivanshos."},
        {"role": "user", "content": "Write a 1-line welcome message confirming system readiness."}
    ]
)

print("\n[Shivanshos Agent Output]")
print(response.choices[0].message.content)
