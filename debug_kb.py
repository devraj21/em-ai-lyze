#!/usr/bin/env python3
"""
Knowledge Base Debugging Script
Helps investigate what's stored in the RAG knowledge base
"""

import json
import sqlite3
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_knowledge_base(kb_path="./email_knowledge_base"):
    """Debug knowledge base contents"""
    print("🔍 Knowledge Base Debugging")
    print("=" * 50)
    
    kb_path = Path(kb_path)
    print(f"📁 Knowledge base path: {kb_path}")
    print(f"📁 Exists: {kb_path.exists()}")
    
    if not kb_path.exists():
        print("❌ Knowledge base directory doesn't exist!")
        print("💡 Try importing some emails first:")
        print("   python -m src.email_parser.rag_cli import /path/to/emails/")
        return
    
    # Check directory contents
    print(f"\n📂 Directory contents:")
    for item in kb_path.iterdir():
        print(f"  • {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    # Check SQLite metadata database
    metadata_db = kb_path / "metadata.db"
    if metadata_db.exists():
        print(f"\n🗄️ SQLite database: {metadata_db}")
        check_sqlite_database(metadata_db)
    else:
        print("\n❌ SQLite metadata database not found")
    
    # Check ChromaDB
    chroma_dir = kb_path / "chroma_db"
    if chroma_dir.exists():
        print(f"\n🔗 ChromaDB directory: {chroma_dir}")
        check_chroma_database(chroma_dir)
    else:
        print("\n❌ ChromaDB directory not found")
    
    # Try RAG CLI stats
    print(f"\n📊 RAG CLI Statistics:")
    try:
        from email_parser.rag_cli import RAGKnowledgeManager
        manager = RAGKnowledgeManager(str(kb_path))
        stats = manager.get_statistics()
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def check_sqlite_database(db_path):
    """Examine SQLite database contents"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if email_knowledge table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='email_knowledge'
        """)
        
        if not cursor.fetchone():
            print("  ❌ email_knowledge table doesn't exist")
            conn.close()
            return
        
        # Count total rows
        cursor.execute("SELECT COUNT(*) FROM email_knowledge")
        total_rows = cursor.fetchone()[0]
        print(f"  📊 Total emails in database: {total_rows}")
        
        if total_rows == 0:
            print("  ⚠️ Database is empty!")
            conn.close()
            return
        
        # Show table schema
        cursor.execute("PRAGMA table_info(email_knowledge)")
        columns = cursor.fetchall()
        print(f"  📋 Table columns: {[col[1] for col in columns]}")
        
        # Show sample data
        cursor.execute("""
            SELECT id, subject, body_summary, categories, timestamp 
            FROM email_knowledge 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        print(f"  📄 Sample emails:")
        for i, row in enumerate(rows, 1):
            email_id, subject, summary, categories, timestamp = row
            print(f"    {i}. {subject[:50]}..." if len(subject or "") > 50 else f"    {i}. {subject}")
            print(f"       Categories: {categories}")
            print(f"       ID: {email_id[:20]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Error reading SQLite database: {e}")

def check_chroma_database(chroma_dir):
    """Examine ChromaDB contents"""
    try:
        import chromadb
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = client.list_collections()
        
        print(f"  📊 ChromaDB collections: {len(collections)}")
        
        for collection in collections:
            print(f"    • Collection: {collection.name}")
            try:
                count = collection.count()
                print(f"      Vectors: {count}")
                
                # Get a few sample documents
                if count > 0:
                    sample = collection.get(limit=3)
                    print(f"      Sample IDs: {sample['ids'][:3] if sample['ids'] else 'None'}")
                    
            except Exception as e:
                print(f"      Error: {e}")
    
    except ImportError:
        print("  ❌ ChromaDB not available")
    except Exception as e:
        print(f"  ❌ Error reading ChromaDB: {e}")

def test_search(kb_path="./email_knowledge_base"):
    """Test search functionality"""
    print(f"\n🔍 Testing Search Functionality")
    print("-" * 30)
    
    try:
        from email_parser.rag_cli import RAGKnowledgeManager
        manager = RAGKnowledgeManager(kb_path)
        
        # Try broad search terms
        test_queries = ["meeting", "email", "budget", "test", "subject"]
        
        for query in test_queries:
            try:
                results = manager.search_knowledge_base(query, max_results=3)
                found = len(results.get('similar_emails', []))
                print(f"  Query '{query}': {found} results")
                
                if found > 0:
                    for email in results['similar_emails'][:2]:
                        print(f"    • {email.get('subject', 'No subject')}")
                        
            except Exception as e:
                print(f"  Query '{query}': Error - {e}")
                
    except Exception as e:
        print(f"❌ Error testing search: {e}")

def list_imported_emails(kb_path="./email_knowledge_base"):
    """List all imported emails with details"""
    print(f"\n📧 All Imported Emails")
    print("-" * 30)
    
    metadata_db = Path(kb_path) / "metadata.db"
    if not metadata_db.exists():
        print("❌ No metadata database found")
        return
    
    try:
        conn = sqlite3.connect(metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, subject, body_summary, categories, entities, timestamp
            FROM email_knowledge 
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 No emails found in database")
            return
        
        print(f"📊 Found {len(rows)} emails:")
        
        for i, row in enumerate(rows, 1):
            email_id, subject, summary, categories, entities, timestamp = row
            
            print(f"\n{i}. EMAIL ID: {email_id}")
            print(f"   Subject: {subject or 'N/A'}")
            print(f"   Summary: {(summary or 'N/A')[:100]}...")
            
            # Parse categories
            try:
                cats = json.loads(categories) if categories else []
                print(f"   Categories: {cats}")
            except:
                print(f"   Categories: {categories}")
            
            # Parse entities  
            try:
                ents = json.loads(entities) if entities else {}
                entity_count = sum(len(v) for v in ents.values() if isinstance(v, list))
                print(f"   Entities: {entity_count} total")
            except:
                print(f"   Entities: Error parsing")
            
            print(f"   Timestamp: {timestamp}")
            
            if i >= 10:  # Limit output
                print(f"\n... and {len(rows) - 10} more emails")
                break
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error listing emails: {e}")

def main():
    """Main debugging function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug RAG Knowledge Base")
    parser.add_argument("--knowledge-base", "-kb", default="./email_knowledge_base",
                       help="Path to knowledge base directory")
    parser.add_argument("--list-emails", "-l", action="store_true",
                       help="List all imported emails")
    parser.add_argument("--test-search", "-s", action="store_true", 
                       help="Test search functionality")
    
    args = parser.parse_args()
    
    # Basic knowledge base check
    check_knowledge_base(args.knowledge_base)
    
    # Optional detailed listing
    if args.list_emails:
        list_imported_emails(args.knowledge_base)
    
    # Optional search testing
    if args.test_search:
        test_search(args.knowledge_base)
    
    print(f"\n💡 Usage Tips:")
    print(f"  • Check if emails were imported: python debug_kb.py --list-emails")
    print(f"  • Test search functionality: python debug_kb.py --test-search")
    print(f"  • Import emails: python -m src.email_parser.rag_cli import /path/to/emails/")

if __name__ == "__main__":
    main()