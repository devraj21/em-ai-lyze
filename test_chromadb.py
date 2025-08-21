#!/usr/bin/env python3
"""
Test ChromaDB vector database directly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_chromadb():
    """Test ChromaDB directly"""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        print("🔍 Testing ChromaDB directly...")
        
        # Connect to the existing ChromaDB
        client = chromadb.PersistentClient('./email_knowledge_base/chroma_db')
        
        # Get the email collection
        collections = client.list_collections()
        print(f"Collections: {[c.name for c in collections]}")
        
        if not collections:
            print("❌ No collections found!")
            return
        
        collection = client.get_collection("email_knowledge")
        count = collection.count()
        print(f"📊 Collection has {count} vectors")
        
        if count == 0:
            print("❌ Collection is empty!")
            return
        
        # Get some sample data
        sample = collection.get(limit=5, include=["documents", "metadatas"])
        print(f"📄 Sample documents:")
        for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
            print(f"  {i+1}. Document: {doc[:100]}...")
            print(f"     Metadata: {meta}")
        
        # Test query with embedding model
        print(f"\n🔍 Testing search...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test queries
        test_queries = ["bupa", "contract", "baby", "restaurant"]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            query_embedding = embedding_model.encode(query).tolist()
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )
            
            print(f"    Results: {len(results['ids'][0]) if results['ids'] else 0}")
            
            if results['ids'] and results['ids'][0]:
                for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    subject = metadata.get('subject', 'No subject')
                    print(f"      {i+1}. {subject} (distance: {distance:.3f})")
            else:
                print("      No results found")
        
        # Check if embeddings are actually stored
        print(f"\n🔢 Checking embeddings...")
        sample_with_embeddings = collection.get(limit=1, include=["embeddings"])
        if sample_with_embeddings['embeddings']:
            embedding = sample_with_embeddings['embeddings'][0]
            print(f"   Sample embedding length: {len(embedding) if embedding else 0}")
            print(f"   Sample embedding values: {embedding[:5] if embedding else 'None'}...")
        else:
            print("   ❌ No embeddings found!")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chromadb()