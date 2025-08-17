"""
RAG (Retrieval-Augmented Generation) Engine for Email Analysis
This module provides contextual knowledge retrieval to enhance email parsing accuracy.
"""

import logging
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    print("Warning: chromadb not installed. Install with: uv pip install chromadb")
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence-transformers not installed. Install with: uv pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EmailKnowledge:
    """Structured knowledge extracted from historical emails"""
    email_id: str
    subject: str
    body_summary: str
    categories: List[str]
    entities: Dict[str, List[str]]
    patterns: Dict[str, Any]
    context: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[datetime] = None


@dataclass
class RAGResult:
    """RAG retrieval result with context and confidence"""
    similar_emails: List[EmailKnowledge]
    context_summary: str
    suggested_categories: List[str]
    confidence_score: float
    relevant_patterns: Dict[str, Any]


class EmailRAGEngine:
    """RAG Engine for contextual email analysis"""
    
    def __init__(self, 
                 knowledge_base_path: str = "./email_knowledge_base",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 max_context_emails: int = 5):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        self.embedding_model_name = embedding_model
        self.max_context_emails = max_context_emails
        
        # Initialize components
        self.embedding_model = None
        self.vector_db = None
        self.metadata_db_path = self.knowledge_base_path / "metadata.db"
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize RAG components"""
        try:
            # Initialize embedding model
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("✅ Embedding model loaded successfully")
            else:
                logger.warning("Sentence transformers not available. RAG will use basic similarity.")
            
            # Initialize vector database
            if CHROMADB_AVAILABLE:
                logger.info("Initializing ChromaDB vector database...")
                self.vector_db = chromadb.PersistentClient(
                    path=str(self.knowledge_base_path / "chroma_db")
                )
                
                # Get or create collection
                try:
                    self.email_collection = self.vector_db.get_collection("email_knowledge")
                    logger.info("✅ Connected to existing email knowledge collection")
                except:
                    self.email_collection = self.vector_db.create_collection(
                        name="email_knowledge",
                        metadata={"description": "Email knowledge base for RAG"}
                    )
                    logger.info("✅ Created new email knowledge collection")
            else:
                logger.warning("ChromaDB not available. Using fallback storage.")
                self.vector_db = None
            
            # Initialize metadata database
            self._initialize_metadata_db()
            
        except Exception as e:
            logger.error(f"Error initializing RAG components: {e}")
            # Continue without RAG capabilities
    
    def _initialize_metadata_db(self):
        """Initialize SQLite database for email metadata"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_knowledge (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    body_summary TEXT,
                    categories TEXT,  -- JSON array
                    entities TEXT,    -- JSON object
                    patterns TEXT,    -- JSON object
                    context TEXT,     -- JSON object
                    timestamp TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_categories ON email_knowledge(categories)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON email_knowledge(timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Metadata database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing metadata database: {e}")
    
    def add_email_knowledge(self, email_content) -> bool:
        """Add email knowledge to the RAG database"""
        try:
            # Generate email ID
            email_id = self._generate_email_id(email_content.subject, email_content.body_text)
            
            # Create knowledge object
            knowledge = EmailKnowledge(
                email_id=email_id,
                subject=email_content.subject,
                body_summary=email_content.ai_summary or email_content.subject,
                categories=email_content.categories,
                entities=email_content.extracted_entities,
                patterns={
                    "correlation_score": email_content.correlation_score,
                    "priority": email_content.ai_priority,
                    "sentiment": email_content.sentiment,
                    "has_attachments": len(email_content.attachments) > 0,
                    "attachment_types": [att.get('file_category', 'unknown') for att in email_content.attachments]
                },
                context={
                    "sender": email_content.sender,
                    "recipients_count": len(email_content.recipients),
                    "body_length": len(email_content.body_text),
                    "subject_length": len(email_content.subject)
                },
                timestamp=email_content.sent_date or datetime.now()
            )
            
            # Generate embedding
            if self.embedding_model:
                combined_text = f"{knowledge.subject} {knowledge.body_summary}"
                knowledge.embedding = self.embedding_model.encode(combined_text).tolist()
            
            # Store in vector database
            if self.vector_db and knowledge.embedding:
                self.email_collection.add(
                    documents=[combined_text],
                    embeddings=[knowledge.embedding],
                    metadatas=[{
                        "email_id": email_id,
                        "subject": knowledge.subject,
                        "categories": json.dumps(knowledge.categories),
                        "timestamp": knowledge.timestamp.isoformat() if knowledge.timestamp else None
                    }],
                    ids=[email_id]
                )
            
            # Store metadata in SQLite
            self._store_metadata(knowledge)
            
            logger.info(f"✅ Added email knowledge: {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding email knowledge: {e}")
            return False
    
    def _generate_email_id(self, subject: str, body: str) -> str:
        """Generate unique ID for email"""
        content = f"{subject}{body}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    def _store_metadata(self, knowledge: EmailKnowledge):
        """Store email metadata in SQLite"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO email_knowledge 
                (id, subject, body_summary, categories, entities, patterns, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                knowledge.email_id,
                knowledge.subject,
                knowledge.body_summary,
                json.dumps(knowledge.categories),
                json.dumps(knowledge.entities),
                json.dumps(knowledge.patterns),
                json.dumps(knowledge.context),
                knowledge.timestamp.isoformat() if knowledge.timestamp else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing metadata: {e}")
    
    def retrieve_context(self, subject: str, body: str, categories: List[str] = None) -> RAGResult:
        """Retrieve relevant context for email analysis"""
        try:
            combined_text = f"{subject} {body[:500]}"  # Limit body for embedding
            
            similar_emails = []
            confidence_score = 0.0
            
            # Vector similarity search
            if self.vector_db and self.embedding_model:
                query_embedding = self.embedding_model.encode(combined_text).tolist()
                
                results = self.email_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=self.max_context_emails,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results['ids'] and results['ids'][0]:
                    for i, email_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][i] if results['distances'] else 1.0
                        similarity = max(0.0, 1.0 - distance)  # Convert distance to similarity
                        
                        if similarity > 0.3:  # Only include reasonably similar emails
                            metadata = self._get_metadata(email_id)
                            if metadata:
                                similar_emails.append(metadata)
                    
                    # Calculate average similarity as confidence
                    if results['distances'] and results['distances'][0]:
                        avg_distance = sum(results['distances'][0]) / len(results['distances'][0])
                        confidence_score = max(0.0, 1.0 - avg_distance)
            
            # Fallback: category-based retrieval
            if not similar_emails and categories:
                similar_emails = self._retrieve_by_categories(categories)
                confidence_score = 0.5  # Medium confidence for category-based retrieval
            
            # Generate context summary and suggestions
            context_summary = self._generate_context_summary(similar_emails)
            suggested_categories = self._suggest_categories(similar_emails, categories)
            relevant_patterns = self._extract_relevant_patterns(similar_emails)
            
            return RAGResult(
                similar_emails=similar_emails,
                context_summary=context_summary,
                suggested_categories=suggested_categories,
                confidence_score=confidence_score,
                relevant_patterns=relevant_patterns
            )
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return RAGResult([], "", [], 0.0, {})
    
    def _get_metadata(self, email_id: str) -> Optional[EmailKnowledge]:
        """Retrieve email metadata by ID"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, subject, body_summary, categories, entities, patterns, context, timestamp
                FROM email_knowledge WHERE id = ?
            """, (email_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return EmailKnowledge(
                    email_id=row[0],
                    subject=row[1],
                    body_summary=row[2],
                    categories=json.loads(row[3]) if row[3] else [],
                    entities=json.loads(row[4]) if row[4] else {},
                    patterns=json.loads(row[5]) if row[5] else {},
                    context=json.loads(row[6]) if row[6] else {},
                    timestamp=datetime.fromisoformat(row[7]) if row[7] else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None
    
    def _retrieve_by_categories(self, categories: List[str]) -> List[EmailKnowledge]:
        """Retrieve emails by categories as fallback"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Build query for category matching
            category_conditions = []
            params = []
            for category in categories:
                category_conditions.append("categories LIKE ?")
                params.append(f'%"{category}"%')
            
            query = f"""
                SELECT id, subject, body_summary, categories, entities, patterns, context, timestamp
                FROM email_knowledge 
                WHERE {' OR '.join(category_conditions)}
                ORDER BY created_at DESC
                LIMIT {self.max_context_emails}
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                knowledge = EmailKnowledge(
                    email_id=row[0],
                    subject=row[1],
                    body_summary=row[2],
                    categories=json.loads(row[3]) if row[3] else [],
                    entities=json.loads(row[4]) if row[4] else {},
                    patterns=json.loads(row[5]) if row[5] else {},
                    context=json.loads(row[6]) if row[6] else {},
                    timestamp=datetime.fromisoformat(row[7]) if row[7] else None
                )
                results.append(knowledge)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving by categories: {e}")
            return []
    
    def _generate_context_summary(self, similar_emails: List[EmailKnowledge]) -> str:
        """Generate context summary from similar emails"""
        if not similar_emails:
            return "No relevant historical context found."
        
        # Analyze patterns in similar emails
        all_categories = []
        common_entities = {}
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for email in similar_emails:
            all_categories.extend(email.categories)
            
            # Count entity types
            for entity_type, entities in email.entities.items():
                if entity_type not in common_entities:
                    common_entities[entity_type] = 0
                common_entities[entity_type] += len(entities)
            
            # Count sentiments
            sentiment = email.patterns.get('sentiment', 'neutral')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        # Generate summary
        most_common_categories = list(set(all_categories))[:3]
        most_common_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        summary = f"Found {len(similar_emails)} similar emails. "
        if most_common_categories:
            summary += f"Common categories: {', '.join(most_common_categories)}. "
        summary += f"Typical sentiment: {most_common_sentiment}."
        
        return summary
    
    def _suggest_categories(self, similar_emails: List[EmailKnowledge], existing_categories: List[str] = None) -> List[str]:
        """Suggest categories based on similar emails"""
        if not similar_emails:
            return existing_categories or []
        
        # Count category occurrences
        category_counts = {}
        for email in similar_emails:
            for category in email.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sort by frequency and get top suggestions
        suggested = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        suggested_categories = [cat for cat, count in suggested[:5]]
        
        # Combine with existing categories
        if existing_categories:
            combined = list(set(existing_categories + suggested_categories))
            return combined[:7]  # Limit total categories
        
        return suggested_categories
    
    def _extract_relevant_patterns(self, similar_emails: List[EmailKnowledge]) -> Dict[str, Any]:
        """Extract relevant patterns from similar emails"""
        if not similar_emails:
            return {}
        
        patterns = {
            "avg_correlation_score": 0.0,
            "common_priorities": {},
            "attachment_patterns": {},
            "sender_patterns": {}
        }
        
        correlation_scores = []
        priorities = {}
        attachment_types = {}
        senders = {}
        
        for email in similar_emails:
            # Correlation scores
            if 'correlation_score' in email.patterns:
                correlation_scores.append(email.patterns['correlation_score'])
            
            # Priorities
            priority = email.patterns.get('priority', 'medium')
            priorities[priority] = priorities.get(priority, 0) + 1
            
            # Attachment types
            for att_type in email.patterns.get('attachment_types', []):
                attachment_types[att_type] = attachment_types.get(att_type, 0) + 1
            
            # Senders
            sender = email.context.get('sender', 'unknown')
            senders[sender] = senders.get(sender, 0) + 1
        
        # Calculate averages and patterns
        if correlation_scores:
            patterns["avg_correlation_score"] = sum(correlation_scores) / len(correlation_scores)
        
        patterns["common_priorities"] = dict(sorted(priorities.items(), key=lambda x: x[1], reverse=True))
        patterns["attachment_patterns"] = dict(sorted(attachment_types.items(), key=lambda x: x[1], reverse=True))
        patterns["sender_patterns"] = dict(sorted(senders.items(), key=lambda x: x[1], reverse=True))
        
        return patterns
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Total emails
            cursor.execute("SELECT COUNT(*) FROM email_knowledge")
            total_emails = cursor.fetchone()[0]
            
            # Category distribution
            cursor.execute("SELECT categories FROM email_knowledge")
            all_categories = []
            for row in cursor.fetchall():
                if row[0]:
                    cats = json.loads(row[0])
                    all_categories.extend(cats)
            
            category_counts = {}
            for cat in all_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            conn.close()
            
            return {
                "total_emails": total_emails,
                "total_categories": len(category_counts),
                "top_categories": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "embedding_model": self.embedding_model_name if self.embedding_model else "None",
                "vector_db_available": self.vector_db is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge stats: {e}")
            return {"error": str(e)}
    
    def clear_knowledge_base(self) -> bool:
        """Clear all knowledge from the database (use with caution)"""
        try:
            # Clear SQLite database
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM email_knowledge")
            conn.commit()
            conn.close()
            
            # Clear ChromaDB collection
            if self.vector_db:
                try:
                    self.vector_db.delete_collection("email_knowledge")
                    self.email_collection = self.vector_db.create_collection(
                        name="email_knowledge",
                        metadata={"description": "Email knowledge base for RAG"}
                    )
                except Exception as e:
                    logger.warning(f"Error clearing vector database: {e}")
            
            logger.info("✅ Knowledge base cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return False