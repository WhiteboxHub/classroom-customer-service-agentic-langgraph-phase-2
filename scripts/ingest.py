import os
import glob
import chromadb
from chromadb.utils import embedding_functions

def ingest_docs():
    print("Starting ingestion...")
    
    # Connect to ChromaDB
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    
    # For local execution without docker, fallback to persistent client if host not reachable
    # But usually inside docker we use HttpClient. 
    # Let's try HttpClient, if it fails (running locally), maybe Print warning.
    
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
    except Exception as e:
        print(f"Could not connect to ChromaDB over HTTP: {e}")
        print("Falling back to local PersistentClient for testing...")
        client = chromadb.PersistentClient(path="./chroma_data_local")

    # Embedding Function (MiniLM runs locally on CPU)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Get or Create Collection
    collection = client.get_or_create_collection(
        name="healthcare_docs",
        embedding_function=ef
    )

    # Read Documents
    docs_dir = "data/raw_docs"
    markdown_files = glob.glob(os.path.join(docs_dir, "*.md"))
    
    documents = []
    metadatas = []
    ids = []
    
    chunk_size = 500
    overlap = 50
    
    doc_count = 0
    chunk_count = 0

    for file_path in markdown_files:
        with open(file_path, "r") as f:
            content = f.read()
            
        filename = os.path.basename(file_path)
        
        # Simple chunking logic
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            
            documents.append(chunk)
            metadatas.append({"source": filename, "chunk_index": chunk_count})
            ids.append(f"{filename}_{chunk_count}")
            
            start += (chunk_size - overlap)
            chunk_count += 1
        
        doc_count += 1

    if documents:
        print(f"Upserting {len(documents)} chunks from {doc_count} documents...")
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingestion Complete: {len(documents)} chunks embedded.")
    else:
        print("No documents found to ingest.")

if __name__ == "__main__":
    ingest_docs()
