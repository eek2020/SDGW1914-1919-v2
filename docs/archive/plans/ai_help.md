# AI Help for 16GB Mac

## 1. The "Sweet Spot" Models for 16GB

To keep your RAG system snappy (over 30 tokens/sec), you should use models that stay under **6–8GB** of RAM.

| Model | Size (Quantized) | Best For... |
| --- | --- | --- |
| **Llama 3.2 (3B)** | ~2.2 GB | **The Speed King.** Instant responses, perfect for simple DB lookups. |
| **Gemma 3 (4B)** | ~2.8 GB | **Logical Accuracy.** Newest 2026 tech from Google; great at following instructions. |
| **Mistral 7B v0.3** | ~4.1 GB | **The All-Rounder.** Still the gold standard for small RAG because it handles "Reasoning" well. |
| **Llama 3.1 (8B)** | ~5.2 GB | **Maximum Intelligence.** The smartest model you can run comfortably without hitting the 16GB limit. |

---

## 2. Recommended Setup for 16GB

Since you have less "breathing room" than the 32GB version, we need to be more efficient.

### Step 1: Use Ollama (Native Mac App)

Download and install [Ollama](https://ollama.com/download). It is highly optimized for the Mac's Metal GPU.

```bash
# In your terminal, pull the best "balance" model for 16GB:
ollama pull llama3.1:8b-instruct-q4_K_M

```

### Step 2: Use a "Tiny" Embedding Model

Embeddings are the part of RAG that turn your DB into math. On 16GB, you don't want a heavy embedding model taking up RAM.

* **Use:** `BAAI/bge-small-en-v1.5`
* **Why:** It only uses about **100MB** of RAM but is very accurate for small-to-medium databases.

### Step 3: Lightweight RAG (Python Script)

This setup uses **LlamaIndex** with **ChromaDB**. It is designed to be "lazy," meaning it only loads what it needs.

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. Setup the "Brain" (Ollama manages the memory here)
llm = Ollama(model="llama3.1:8b", request_timeout=120.0)

# 2. Setup the "Librarian" (Fast & Tiny)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 3. Load your small DB (e.g., a folder with your CSV or .txt exports)
documents = SimpleDirectoryReader("./my_data").load_data()

# 4. Build the searchable index
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

# 5. Chat with your DB
query_engine = index.as_query_engine(llm=llm)
response = query_engine.query("Summarize the most frequent entries in my database.")
print(response)

```

---

## 3. Important 16GB "Survival" Tips

* **Close Chrome:** Browsers are RAM vampires. If you have 20 tabs open, your 16GB Mac only has about 4GB left for the AI, which will force it to be slow.
* **Avoid "Thinking" Models:** In 2026, some models (like DeepSeek R1 or Qwen Thinking) use extra RAM for "Chain of Thought." On 16GB, stick to "Instruct" or "Dense" models for better stability.
* **Quantization is Mandatory:** Never download a "Full" or "FP16" model. Only use versions with `q4_K_M` or `q5_0` in the name. They reduce memory usage by 70% with almost zero loss in "smartness."

**If your database is in a specific format (like a SQL export or a massive Excel sheet), would you like me to show you how to "chunk" it so it fits better in your 16GB RAM?**
