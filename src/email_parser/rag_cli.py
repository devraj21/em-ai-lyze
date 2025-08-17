"""
RAG Knowledge Base Management CLI
Command-line interface for managing the email knowledge base.
"""

import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    from .rag_engine import EmailRAGEngine
    from .parser import EmailParser
    RAG_CLI_AVAILABLE = True
except ImportError:
    print("Warning: RAG components not available")
    RAG_CLI_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGKnowledgeManager:
    """Knowledge base management utilities"""
    
    def __init__(self, knowledge_base_path: str = "./email_knowledge_base"):
        if not RAG_CLI_AVAILABLE:
            raise ImportError("RAG components not available")
        
        self.knowledge_base_path = Path(knowledge_base_path)
        self.rag_engine = EmailRAGEngine(knowledge_base_path=knowledge_base_path)
        self.email_parser = EmailParser(use_rag=True, knowledge_base_path=knowledge_base_path)
    
    def import_emails_from_folder(self, folder_path: str, file_pattern: str = "*.msg") -> Dict[str, Any]:
        """Import all emails from a folder into the knowledge base"""
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}
        
        email_files = list(folder.glob(file_pattern))
        results = {
            "total_files": len(email_files),
            "processed": 0,
            "failed": 0,
            "errors": []
        }
        
        print(f"🔄 Importing {len(email_files)} email files from {folder_path}")
        
        for email_file in email_files:
            try:
                print(f"   Processing: {email_file.name}")
                
                # Parse email with RAG disabled during import to avoid circular dependency
                temp_parser = EmailParser(use_rag=False)
                email_content = temp_parser.parse_msg_file(email_file)
                
                if email_content:
                    # Add to knowledge base
                    success = self.rag_engine.add_email_knowledge(email_content)
                    if success:
                        results["processed"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to store: {email_file.name}")
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to parse: {email_file.name}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error processing {email_file.name}: {str(e)}")
                logger.error(f"Error processing {email_file.name}: {e}")
        
        print(f"✅ Import completed: {results['processed']} processed, {results['failed']} failed")
        return results
    
    def search_knowledge_base(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search the knowledge base for similar emails"""
        try:
            rag_result = self.rag_engine.retrieve_context(
                subject=query,
                body="",
                categories=[]
            )
            
            results = {
                "query": query,
                "similar_emails": [],
                "context_summary": rag_result.context_summary,
                "confidence": rag_result.confidence_score
            }
            
            for email in rag_result.similar_emails[:max_results]:
                results["similar_emails"].append({
                    "id": email.email_id,
                    "subject": email.subject,
                    "summary": email.body_summary,
                    "categories": email.categories,
                    "timestamp": email.timestamp.isoformat() if email.timestamp else None
                })
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return self.rag_engine.get_knowledge_stats()
    
    def export_knowledge_base(self, output_file: str) -> Dict[str, Any]:
        """Export knowledge base to JSON file"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.rag_engine.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, subject, body_summary, categories, entities, patterns, context, timestamp
                FROM email_knowledge
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            exported_data = []
            for row in rows:
                exported_data.append({
                    "id": row[0],
                    "subject": row[1],
                    "body_summary": row[2],
                    "categories": json.loads(row[3]) if row[3] else [],
                    "entities": json.loads(row[4]) if row[4] else {},
                    "patterns": json.loads(row[5]) if row[5] else {},
                    "context": json.loads(row[6]) if row[6] else {},
                    "timestamp": row[7]
                })
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump({
                    "export_date": str(Path().cwd()),
                    "total_emails": len(exported_data),
                    "emails": exported_data
                }, f, indent=2, default=str)
            
            return {
                "success": True,
                "exported_emails": len(exported_data),
                "output_file": output_file
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all knowledge from the database"""
        try:
            success = self.rag_engine.clear_knowledge_base()
            return {"success": success}
        except Exception as e:
            return {"error": str(e)}
    
    def test_rag_retrieval(self, test_subject: str, test_body: str) -> Dict[str, Any]:
        """Test RAG retrieval with sample content"""
        try:
            # Parse test email
            temp_parser = EmailParser(use_rag=True, knowledge_base_path=str(self.knowledge_base_path))
            
            # Create a mock email content for testing
            from datetime import datetime
            from .parser import EmailContent
            
            mock_email = EmailContent(
                message_id="test_email",
                subject=test_subject,
                sender="test@example.com",
                recipients=["recipient@example.com"],
                cc_recipients=[],
                bcc_recipients=[],
                sent_date=datetime.now(),
                body_text=test_body,
                body_html="",
                attachments=[],
                priority="normal",
                categories=[],
                correlation_score=0.5,
                extracted_entities={},
                standardized_format={}
            )
            
            # Get RAG context
            rag_result = self.rag_engine.retrieve_context(
                subject=test_subject,
                body=test_body,
                categories=[]
            )
            
            return {
                "test_subject": test_subject,
                "test_body": test_body[:100] + "..." if len(test_body) > 100 else test_body,
                "similar_emails_found": len(rag_result.similar_emails),
                "context_summary": rag_result.context_summary,
                "suggested_categories": rag_result.suggested_categories,
                "confidence_score": rag_result.confidence_score,
                "relevant_patterns": rag_result.relevant_patterns
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main CLI entry point"""
    if not RAG_CLI_AVAILABLE:
        print("❌ RAG components not available. Please install required dependencies.")
        return
    
    parser = argparse.ArgumentParser(description="RAG Knowledge Base Management CLI")
    parser.add_argument("--knowledge-base", "-k", default="./email_knowledge_base",
                       help="Path to knowledge base directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import emails from folder")
    import_parser.add_argument("folder", help="Folder containing .msg files")
    import_parser.add_argument("--pattern", default="*.msg", help="File pattern to match")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max-results", "-n", type=int, default=5, help="Max results")
    
    # Stats command
    subparsers.add_parser("stats", help="Show knowledge base statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export knowledge base")
    export_parser.add_argument("output", help="Output JSON file")
    
    # Clear command
    subparsers.add_parser("clear", help="Clear knowledge base (DANGEROUS)")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test RAG retrieval")
    test_parser.add_argument("subject", help="Test email subject")
    test_parser.add_argument("body", help="Test email body")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = RAGKnowledgeManager(args.knowledge_base)
        
        if args.command == "import":
            result = manager.import_emails_from_folder(args.folder, args.pattern)
            print(json.dumps(result, indent=2))
            
        elif args.command == "search":
            result = manager.search_knowledge_base(args.query, args.max_results)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == "stats":
            result = manager.get_statistics()
            print(json.dumps(result, indent=2))
            
        elif args.command == "export":
            result = manager.export_knowledge_base(args.output)
            print(json.dumps(result, indent=2))
            
        elif args.command == "clear":
            confirm = input("⚠️  This will delete ALL knowledge base data. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                result = manager.clear_knowledge_base()
                print(json.dumps(result, indent=2))
            else:
                print("Operation cancelled.")
                
        elif args.command == "test":
            result = manager.test_rag_retrieval(args.subject, args.body)
            print(json.dumps(result, indent=2, default=str))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"CLI Error: {e}")


if __name__ == "__main__":
    main()