"""
Email parsing functionality for MCP Server
This module provides the EmailParser class to parse .msg files and extract structured email content.
It includes methods for parsing recipients, extracting entities, calculating correlation scores,
categorizing emails, and generating standardized formats.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

try:
    import extract_msg
except ImportError:
    print("Warning: extract_msg not installed. Install with: uv pip install extract-msg")
    extract_msg = None

try:
    from .ai_extractor import AIEmailExtractor, EmailStructuredData
    AI_AVAILABLE = True
except ImportError:
    print("Warning: AI extraction not available. Install with: uv pip install 'email-parsing-mcp[ai]'")
    AI_AVAILABLE = False
    AIEmailExtractor = None
    EmailStructuredData = None

try:
    from .rag_engine import EmailRAGEngine, RAGResult
    RAG_AVAILABLE = True
except ImportError:
    print("Warning: RAG engine not available. Some dependencies may be missing.")
    RAG_AVAILABLE = False
    EmailRAGEngine = None
    RAGResult = None

logger = logging.getLogger(__name__)

@dataclass
class EmailContent:
    """Standardized email content structure"""
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc_recipients: List[str]
    bcc_recipients: List[str]
    sent_date: Optional[datetime]
    body_text: str
    body_html: str
    attachments: List[Dict[str, Any]]
    priority: str
    categories: List[str]
    correlation_score: float
    extracted_entities: Dict[str, List[str]]
    standardized_format: Dict[str, Any]
    # New AI-enhanced fields
    ai_structured_data: Optional[Any] = None  # EmailStructuredData when AI available
    sentiment: str = "neutral"
    ai_summary: str = ""
    ai_priority: str = "medium"
    
    # RAG-enhanced fields
    rag_context: Optional[Any] = None  # RAGResult when RAG available
    context_summary: str = ""
    suggested_categories: List[str] = None
    knowledge_confidence: float = 0.0

class EmailParser:
    """Main email parsing engine"""
    
    def __init__(self, use_ai: bool = True, ai_model: str = "gemini-1.5-flash", use_local: bool = False, 
                 use_rag: bool = True, knowledge_base_path: str = "./email_knowledge_base"):
        self.supported_extensions = ['.msg']
        self.use_ai = use_ai and AI_AVAILABLE
        self.use_local = use_local
        self.use_rag = use_rag and RAG_AVAILABLE
        
        # Initialize AI extractor if available
        if self.use_ai:
            try:
                self.ai_extractor = AIEmailExtractor(model_id=ai_model, use_local=use_local)
                model_type = "local" if use_local else "cloud"
                logger.info(f"AI extraction enabled with {model_type} model: {self.ai_extractor.model_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize AI extractor: {e}")
                self.ai_extractor = None
                self.use_ai = False
        else:
            self.ai_extractor = None
            logger.info("Using traditional regex-based extraction")
        
        # Initialize RAG engine if available
        if self.use_rag:
            try:
                self.rag_engine = EmailRAGEngine(knowledge_base_path=knowledge_base_path)
                logger.info(f"RAG engine enabled with knowledge base: {knowledge_base_path}")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG engine: {e}")
                self.rag_engine = None
                self.use_rag = False
        else:
            self.rag_engine = None
            logger.info("RAG engine disabled")
        
        # Fixed and improved regex patterns (fallback)
        self.entity_patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'phones': r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'dates': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            'urls': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            'money': r'(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?))',
        }
    
    def parse_msg_file(self, file_path: Path) -> Optional[EmailContent]:
        """Parse a .msg file and extract content"""
        if extract_msg is None:
            logger.error("extract_msg not available. Cannot parse .msg files.")
            return None
            
        try:
            logger.info(f"Parsing email file: {file_path}")
            
            # Extract message using extract_msg
            msg = extract_msg.Message(str(file_path))
            
            # Extract basic information
            subject = msg.subject or ""
            sender = msg.sender or ""
            recipients = self._parse_recipients(msg.to)
            cc_recipients = self._parse_recipients(msg.cc)
            bcc_recipients = self._parse_recipients(msg.bcc)
            
            # Parse date
            sent_date = None
            if msg.date:
                try:
                    if isinstance(msg.date, str):
                        sent_date = parsedate_to_datetime(msg.date)
                    else:
                        sent_date = msg.date
                except Exception as e:
                    logger.warning(f"Could not parse date: {e}")
            
            # Extract body content
            body_text = msg.body or ""
            body_html = getattr(msg, 'htmlBody', '') or ""
            
            # Extract attachments
            attachments = self._extract_attachments(msg)
            
            # RAG-Enhanced Context Retrieval
            rag_context = None
            context_summary = ""
            suggested_categories = []
            knowledge_confidence = 0.0
            
            if self.use_rag and self.rag_engine:
                try:
                    # Get initial categories for context retrieval
                    initial_categories = self._categorize_email(subject, body_text, attachments)
                    
                    # Retrieve relevant context from knowledge base
                    rag_context = self.rag_engine.retrieve_context(
                        subject=subject,
                        body=body_text,
                        categories=initial_categories
                    )
                    
                    context_summary = rag_context.context_summary
                    suggested_categories = rag_context.suggested_categories
                    knowledge_confidence = rag_context.confidence_score
                    
                    logger.info(f"RAG context retrieved: confidence={knowledge_confidence:.3f}, similar_emails={len(rag_context.similar_emails)}")
                    
                except Exception as e:
                    logger.warning(f"RAG context retrieval failed: {e}")
            
            # AI-Enhanced Processing with RAG Context
            ai_structured_data = None
            ai_summary = ""
            ai_priority = "medium"
            sentiment = "neutral"
            
            if self.use_ai and self.ai_extractor:
                try:
                    # Pass RAG context to AI extractor for enhanced analysis
                    ai_structured_data = self.ai_extractor.extract_structured_data(
                        subject, body_text, sender, recipients, attachments, rag_context
                    )
                    ai_summary = ai_structured_data.summary
                    ai_priority = ai_structured_data.priority_level
                    sentiment = ai_structured_data.sentiment
                    
                    # Combine AI-extracted entities and categories with RAG suggestions
                    extracted_entities = ai_structured_data.entities
                    categories = self._merge_categories(ai_structured_data.categories, suggested_categories)
                    
                    logger.info("Successfully applied AI extraction with RAG context")
                except Exception as e:
                    logger.warning(f"AI extraction failed, falling back to regex: {e}")
                    # Fallback to traditional extraction with RAG suggestions
                    combined_text = f"{subject} {body_text}"
                    extracted_entities = self._extract_entities(combined_text)
                    base_categories = self._categorize_email(subject, body_text, attachments)
                    categories = self._merge_categories(base_categories, suggested_categories)
            else:
                # Traditional extraction with RAG suggestions
                combined_text = f"{subject} {body_text}"
                extracted_entities = self._extract_entities(combined_text)
                base_categories = self._categorize_email(subject, body_text, attachments)
                categories = self._merge_categories(base_categories, suggested_categories)
            
            # Calculate correlation score
            correlation_score = self._calculate_correlation(subject, body_text, attachments)
            
            # Create standardized format (enhanced with AI data if available)
            standardized_format = self._create_standardized_format(
                subject, body_text, attachments, extracted_entities, ai_structured_data
            )
            
            email_content = EmailContent(
                message_id=getattr(msg, 'messageId', '') or str(file_path.name),
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients,
                sent_date=sent_date,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                priority=getattr(msg, 'importance', 'normal'),
                categories=categories,
                correlation_score=correlation_score,
                extracted_entities=extracted_entities,
                standardized_format=standardized_format,
                # AI-enhanced fields
                ai_structured_data=ai_structured_data,
                sentiment=sentiment,
                ai_summary=ai_summary,
                ai_priority=ai_priority,
                # RAG-enhanced fields
                rag_context=rag_context,
                context_summary=context_summary,
                suggested_categories=suggested_categories,
                knowledge_confidence=knowledge_confidence
            )
            
            # Store this email in RAG knowledge base for future reference
            if self.use_rag and self.rag_engine:
                try:
                    self.rag_engine.add_email_knowledge(email_content)
                    logger.info("Email knowledge stored for future RAG retrieval")
                except Exception as e:
                    logger.warning(f"Failed to store email knowledge: {e}")
            
            logger.info(f"Successfully parsed email: {subject[:50]}...")
            return email_content
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return None
    
    def _parse_recipients(self, recipients_str: Optional[str]) -> List[str]:
        """Parse recipients string into list"""
        if not recipients_str:
            return []
        
        # Split by common delimiters and clean up
        recipients = re.split(r'[;,]\s*', recipients_str)
        return [r.strip() for r in recipients if r.strip()]
    
    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        """Extract attachment information with content analysis"""
        attachments = []
        
        try:
            for attachment in msg.attachments:
                filename = getattr(attachment, 'longFilename', '') or getattr(attachment, 'shortFilename', '')
                content_type = getattr(attachment, 'mimetype', '')
                size = getattr(attachment, 'size', 0)
                
                att_info = {
                    'filename': filename,
                    'size': size,
                    'content_type': content_type,
                    'is_embedded': hasattr(attachment, 'cid'),
                    'content_preview': '',
                    'content_summary': '',
                    'extracted_text': '',
                    'file_category': self._categorize_file_type(filename, content_type),
                }
                
                # Extract content from readable file types
                try:
                    att_info['extracted_text'] = self._extract_attachment_content(attachment, filename, content_type)
                    if att_info['extracted_text']:
                        att_info['content_preview'] = att_info['extracted_text'][:200] + ('...' if len(att_info['extracted_text']) > 200 else '')
                        # Generate AI summary if available
                        if self.use_ai and self.ai_extractor and att_info['extracted_text'].strip():
                            att_info['content_summary'] = self._summarize_attachment_content(att_info['extracted_text'])
                except Exception as e:
                    logger.warning(f"Error extracting content from attachment {filename}: {e}")
                
                attachments.append(att_info)
        except Exception as e:
            logger.warning(f"Error extracting attachments: {e}")
        
        return attachments
    
    def _categorize_file_type(self, filename: str, content_type: str) -> str:
        """Categorize file type for better analysis"""
        if not filename:
            return 'unknown'
        
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Document types
        if ext in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']:
            return 'document'
        # Spreadsheet types
        elif ext in ['xls', 'xlsx', 'csv', 'ods']:
            return 'spreadsheet'
        # Image types
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg']:
            return 'image'
        # Presentation types
        elif ext in ['ppt', 'pptx', 'odp']:
            return 'presentation'
        # Code/text files
        elif ext in ['py', 'js', 'html', 'css', 'json', 'xml', 'sql']:
            return 'code'
        # Archive types
        elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
            return 'archive'
        # Media types
        elif ext in ['mp4', 'avi', 'mkv', 'mp3', 'wav', 'flac']:
            return 'media'
        else:
            return 'other'
    
    def _extract_attachment_content(self, attachment, filename: str, content_type: str) -> str:
        """Extract readable content from attachments"""
        try:
            # Only extract from text-readable files to avoid binary data
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            # Text files that can be safely read
            text_extensions = ['txt', 'csv', 'json', 'xml', 'html', 'htm', 'py', 'js', 'css', 'sql', 'log']
            
            if file_ext in text_extensions:
                # Get attachment data
                if hasattr(attachment, 'data') and attachment.data:
                    try:
                        # Try to decode as UTF-8 text
                        content = attachment.data.decode('utf-8', errors='ignore')
                        return content[:5000]  # Limit to first 5000 characters
                    except Exception:
                        # Try other common encodings
                        for encoding in ['latin1', 'cp1252', 'ascii']:
                            try:
                                content = attachment.data.decode(encoding, errors='ignore')
                                return content[:5000]
                            except Exception:
                                continue
            
            # For other file types, return empty string (could be extended with specialized libraries)
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting content from {filename}: {e}")
            return ""
    
    def _summarize_attachment_content(self, content: str) -> str:
        """Generate AI summary of attachment content"""
        try:
            if not content.strip() or not self.use_ai or not self.ai_extractor:
                return ""
            
            summary_prompt = """
            Provide a concise 1-2 sentence summary of this attachment content.
            Focus on the main purpose, key information, or primary topic.
            Keep it brief and informative.
            """
            
            import langextract as lx
            
            result = lx.extract(
                text_or_documents=content[:1000],  # Limit content for summary
                prompt_description=summary_prompt,
                examples=[],
                model_id=self.ai_extractor.model_id
            )
            
            # Extract summary from result
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    if hasattr(extraction, 'extraction_text'):
                        summary = str(extraction.extraction_text).strip()
                        if summary:
                            return summary[:200]  # Limit summary length
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error generating attachment summary: {e}")
            return ""
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using regex patterns"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                # Filter out empty strings and duplicates
                entities[entity_type] = list(set([match.strip() for match in matches if match.strip()]))
            except Exception as e:
                logger.warning(f"Error in pattern {entity_type}: {e}")
                entities[entity_type] = []
        
        return entities
    
    def _calculate_correlation(self, subject: str, body: str, attachments: List[Dict]) -> float:
        """Calculate enhanced correlation score between subject, body, and attachments"""
        try:
            # Use AI-enhanced semantic correlation if available
            if self.use_ai and self.ai_extractor:
                return self._calculate_ai_correlation(subject, body, attachments)
            else:
                return self._calculate_basic_correlation(subject, body, attachments)
        except Exception as e:
            logger.warning(f"Error calculating correlation, using basic method: {e}")
            return self._calculate_basic_correlation(subject, body, attachments)
    
    def _calculate_ai_correlation(self, subject: str, body: str, attachments: List[Dict]) -> float:
        """AI-enhanced semantic correlation analysis with simplified approach"""
        try:
            # Use a simpler, more reliable approach for correlation analysis
            correlation_prompt = f"""
            Rate the correlation between these email components on a scale from 0.0 to 1.0:
            
            Subject: "{subject}"
            Body: "{body[:500]}{'...' if len(body) > 500 else ''}"
            Attachments: {len(attachments)} files - {', '.join([att.get('filename', 'unnamed') for att in attachments[:3]])}
            
            Score meanings:
            - 0.9-1.0: Perfect alignment (all components discuss same topic)
            - 0.7-0.8: High correlation (strongly related topics)
            - 0.5-0.6: Medium correlation (some relationship)
            - 0.3-0.4: Low correlation (minimal relationship)
            - 0.0-0.2: No correlation (unrelated content)
            
            Respond with just the numeric score (e.g., 0.75).
            """
            
            # Skip AI correlation for now and use enhanced basic correlation
            # The LangExtract structured extraction is too complex for correlation scoring
            logger.info("Skipping AI correlation, using enhanced basic correlation")
            
            # If AI fails, use enhanced basic correlation with better logic
            logger.info("Using enhanced basic correlation analysis")
            return self._calculate_enhanced_basic_correlation(subject, body, attachments)
            
        except Exception as e:
            logger.warning(f"AI correlation analysis failed: {e}")
            return self._calculate_basic_correlation(subject, body, attachments)
    
    def _calculate_enhanced_basic_correlation(self, subject: str, body: str, attachments: List[Dict]) -> float:
        """Enhanced basic correlation with better semantic understanding"""
        score = 0.0
        
        # Clean and prepare text
        subject_clean = ' '.join(subject.lower().split())
        body_clean = ' '.join(body.lower().split())
        
        # Extract meaningful words (longer than 3 chars, not common words)
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'what', 'when', 'your', 'said', 'each', 'make', 'most', 'over', 'said', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
        
        subject_words = set([w for w in re.findall(r'\w{4,}', subject_clean) if w not in stop_words])
        body_words = set([w for w in re.findall(r'\w{4,}', body_clean) if w not in stop_words])
        
        # Subject-Body correlation with weight for word length
        if subject_words and body_words:
            common_words = subject_words.intersection(body_words)
            if common_words:
                # Weight by average word length (longer words are more meaningful)
                avg_length = sum(len(word) for word in common_words) / len(common_words)
                length_factor = min(1.5, avg_length / 6)  # Boost for longer words
                
                base_score = len(common_words) / len(subject_words)
                score += base_score * length_factor * 0.8  # 80% weight for subject-body
        
        # Subject-Attachment correlation
        if attachments:
            att_scores = []
            for att in attachments:
                att_score = 0.0
                filename = att.get('filename', '').lower()
                file_category = att.get('file_category', '')
                content_summary = att.get('content_summary', '').lower()
                
                # Filename-subject correlation
                if filename:
                    filename_words = set(re.findall(r'\w{3,}', filename))
                    filename_common = filename_words.intersection(subject_words)
                    if filename_common:
                        att_score += len(filename_common) / max(len(subject_words), 1) * 0.4
                
                # Content summary correlation
                if content_summary:
                    summary_words = set(re.findall(r'\w{4,}', content_summary))
                    summary_common = summary_words.intersection(subject_words.union(body_words))
                    if summary_common:
                        att_score += len(summary_common) / max(len(subject_words) + len(body_words), 1) * 0.6
                
                # Contextual relevance based on file type and subject
                context_boost = self._get_context_relevance_boost(subject_clean, file_category)
                att_score += context_boost
                
                att_scores.append(min(att_score, 1.0))
            
            # Average attachment correlation with reduced weight
            if att_scores:
                avg_att_score = sum(att_scores) / len(att_scores)
                score += avg_att_score * 0.2  # 20% weight for attachments
        
        # Quality penalties and bonuses
        if len(subject.strip()) < 5:
            score *= 0.7  # Penalty for very short subjects
        if len(body.strip()) < 20:
            score *= 0.8  # Penalty for very short bodies
            
        # Bonus for well-structured content
        if ':' in subject or '-' in subject:  # Structured subjects
            score *= 1.1
        
        return min(score, 1.0)
    
    def _get_context_relevance_boost(self, subject: str, file_category: str) -> float:
        """Get context relevance boost based on subject content and file type"""
        boost = 0.0
        
        context_mappings = {
            'document': ['report', 'document', 'memo', 'proposal', 'contract', 'agreement'],
            'spreadsheet': ['budget', 'data', 'analysis', 'financial', 'numbers', 'calculation'],
            'image': ['photo', 'image', 'screenshot', 'picture', 'diagram', 'chart'],
            'presentation': ['presentation', 'slides', 'meeting', 'demo', 'overview']
        }
        
        if file_category in context_mappings:
            keywords = context_mappings[file_category]
            if any(keyword in subject for keyword in keywords):
                boost = 0.15  # 15% boost for contextual relevance
        
        return boost
    
    def _calculate_basic_correlation(self, subject: str, body: str, attachments: List[Dict]) -> float:
        """Basic correlation analysis using word overlap (fallback method)"""
        score = 0.0
        
        # Enhanced subject-body correlation with better text processing
        subject_words = set(re.findall(r'\w+', subject.lower()))
        body_words = set(re.findall(r'\w+', body.lower()))
        
        # Remove common stop words for better correlation
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'do', 'does', 'did', 'get', 'got', 'go', 'went', 'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'say', 'said', 'tell', 'told', 'ask', 'asked', 'give', 'gave', 'take', 'took', 'make', 'made', 'find', 'found', 'look', 'looked', 'use', 'used', 'want', 'wanted', 'need', 'needed', 'try', 'tried', 'work', 'worked', 'call', 'called', 'put', 'put', 'end', 'ended', 'why', 'what', 'where', 'when', 'who', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'here', 'there', 'then', 'them', 'they', 'their', 'this', 'that', 'these', 'those', 'he', 'she', 'it', 'we', 'you', 'i', 'me', 'my', 'your', 'his', 'her', 'its', 'our'}
        
        subject_words_filtered = subject_words - stop_words
        body_words_filtered = body_words - stop_words
        
        if subject_words_filtered and body_words_filtered:
            common_words = subject_words_filtered.intersection(body_words_filtered)
            # Enhanced scoring considering word importance
            if common_words:
                word_score = len(common_words) / max(len(subject_words_filtered), len(body_words_filtered))
                # Boost score for longer common words (more meaningful)
                length_boost = sum(len(word) for word in common_words) / (len(common_words) * 10)  # Normalize by average word length
                score += word_score + (length_boost * 0.1)
        
        # Enhanced subject-attachment correlation
        if attachments:
            attachment_scores = []
            for att in attachments:
                att_score = 0.0
                filename = att.get('filename', '').lower()
                
                if filename:
                    # Filename correlation
                    name_words = set(re.findall(r'\w+', filename)) - stop_words
                    if name_words and subject_words_filtered:
                        name_common = name_words.intersection(subject_words_filtered)
                        if name_common:
                            att_score += len(name_common) / len(subject_words_filtered)
                    
                    # File type relevance to subject
                    file_ext = filename.split('.')[-1] if '.' in filename else ''
                    subject_lower = subject.lower()
                    
                    # Context-based file relevance
                    doc_indicators = ['report', 'document', 'proposal', 'contract', 'agreement']
                    image_indicators = ['photo', 'image', 'screenshot', 'diagram', 'chart']
                    spreadsheet_indicators = ['budget', 'data', 'analysis', 'numbers', 'financial']
                    
                    if file_ext in ['pdf', 'doc', 'docx'] and any(ind in subject_lower for ind in doc_indicators):
                        att_score += 0.3
                    elif file_ext in ['jpg', 'png', 'gif', 'bmp'] and any(ind in subject_lower for ind in image_indicators):
                        att_score += 0.3
                    elif file_ext in ['xls', 'xlsx', 'csv'] and any(ind in subject_lower for ind in spreadsheet_indicators):
                        att_score += 0.3
                
                attachment_scores.append(att_score)
            
            # Average attachment correlation, weighted less than subject-body
            if attachment_scores:
                avg_att_score = sum(attachment_scores) / len(attachment_scores)
                score += avg_att_score * 0.3  # Reduced weight for attachments
        
        # Penalize very short subjects or bodies (likely spam or incomplete)
        if len(subject.strip()) < 3 or len(body.strip()) < 10:
            score *= 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _merge_categories(self, base_categories: List[str], suggested_categories: List[str]) -> List[str]:
        """Merge base categories with RAG-suggested categories"""
        if not suggested_categories:
            return base_categories
        
        # Combine and deduplicate categories
        combined = list(set(base_categories + suggested_categories))
        
        # Prioritize certain categories
        priority_categories = ['urgent', 'important', 'meeting', 'invoice', 'contract']
        prioritized = []
        regular = []
        
        for cat in combined:
            if cat in priority_categories:
                prioritized.append(cat)
            else:
                regular.append(cat)
        
        # Limit total categories to prevent overflow
        final_categories = prioritized + regular
        return final_categories[:8]  # Limit to 8 categories max
    
    def _categorize_email(self, subject: str, body: str, attachments: List[Dict]) -> List[str]:
        """Categorize email based on content"""
        categories = []
        content = f"{subject} {body}".lower()
        
        # Define category keywords
        category_keywords = {
            'meeting': ['meeting', 'conference', 'call', 'appointment', 'schedule'],
            'invoice': ['invoice', 'bill', 'payment', 'amount due', 'billing'],
            'report': ['report', 'analysis', 'summary', 'findings', 'results'],
            'urgent': ['urgent', 'asap', 'immediate', 'critical', 'emergency'],
            'follow_up': ['follow up', 'followup', 'reminder', 'checking in'],
            'contract': ['contract', 'agreement', 'terms', 'legal', 'signature'],
            'support': ['help', 'support', 'issue', 'problem', 'assistance'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content for keyword in keywords):
                categories.append(category)
        
        # Check for attachments
        if attachments:
            categories.append('has_attachments')
            
            # Specific attachment types
            for att in attachments:
                filename = att.get('filename', '').lower()
                if filename.endswith(('.pdf', '.doc', '.docx')):
                    categories.append('document')
                elif filename.endswith(('.jpg', '.png', '.gif', '.bmp')):
                    categories.append('image')
                elif filename.endswith(('.xls', '.xlsx', '.csv')):
                    categories.append('spreadsheet')
        
        return categories or ['general']
    
    def _create_standardized_format(self, subject: str, body: str, 
                                  attachments: List[Dict], entities: Dict,
                                  ai_data: Optional[Any] = None) -> Dict[str, Any]:
        """Create standardized format for the email"""
        if ai_data and hasattr(ai_data, 'summary'):
            # Use AI-enhanced data when available
            return {
                'summary': ai_data.summary,
                'key_points': ai_data.key_points,
                'action_items': [item.get('task', str(item)) if isinstance(item, dict) else str(item) for item in ai_data.action_items],
                'mentioned_people': [person.get('name', str(person)) if isinstance(person, dict) else str(person) for person in ai_data.people_mentioned],
                'mentioned_dates': [date.get('date', str(date)) if isinstance(date, dict) else str(date) for date in ai_data.dates_mentioned],
                'mentioned_amounts': [amount.get('amount', str(amount)) if isinstance(amount, dict) else str(amount) for amount in ai_data.monetary_amounts],
                'attachment_summary': self._summarize_attachments(attachments),
                'priority_indicators': [ai_data.priority_level],
                'sentiment': ai_data.sentiment,
                'categories': ai_data.categories,
                'meeting_details': ai_data.meeting_details,
                'contact_information': ai_data.contact_information,
                'ai_enhanced': True
            }
        else:
            # Fallback to traditional extraction
            return {
                'summary': self._generate_summary(subject, body),
                'key_points': self._extract_key_points(body),
                'action_items': self._extract_action_items(body),
                'mentioned_people': entities.get('emails', []),
                'mentioned_dates': entities.get('dates', []),
                'mentioned_amounts': entities.get('money', []),
                'attachment_summary': self._summarize_attachments(attachments),
                'priority_indicators': self._identify_priority_indicators(subject, body),
                'sentiment': 'neutral',
                'categories': [],
                'meeting_details': None,
                'contact_information': [],
                'ai_enhanced': False
            }
    
    def _generate_summary(self, subject: str, body: str) -> str:
        """Generate a brief summary of the email"""
        # Simple extractive summary - take first sentence of body
        sentences = re.split(r'[.!?]+', body.strip())
        first_sentence = sentences[0].strip() if sentences else ""
        
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:97] + "..."
        
        return f"Re: {subject}. {first_sentence}" if first_sentence else subject
    
    def _extract_key_points(self, body: str) -> List[str]:
        """Extract key points from email body"""
        # Look for bullet points, numbered lists, or sentences with key indicators
        key_points = []
        
        # Bullet points - improved regex
        bullet_matches = re.findall(r'[•\-\*]\s*(.+?)(?=\n|$)', body, re.MULTILINE)
        key_points.extend([match.strip() for match in bullet_matches if match.strip()])
        
        # Numbered lists - improved regex
        numbered_matches = re.findall(r'\d+[\.\)]\s*(.+?)(?=\n|$)', body, re.MULTILINE)
        key_points.extend([match.strip() for match in numbered_matches if match.strip()])
        
        # Key indicator phrases
        key_indicators = ['important', 'note that', 'please', 'action required', 'deadline']
        sentences = re.split(r'[.!?]+', body)
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:  # Avoid very short fragments
                    key_points.append(clean_sentence)
        
        return key_points[:5]  # Limit to top 5
    
    def _extract_action_items(self, body: str) -> List[str]:
        """Extract action items from email body"""
        action_items = []
        action_patterns = [
            r'(?:please|could you|can you|need to|must|should)\s+(.+?)(?:[.!?]|$)',
            r'action\s*(?:item|required):\s*(.+?)(?:[.!?]|$)',
            r'to\s*do:\s*(.+?)(?:[.!?]|$)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE | re.MULTILINE)
            action_items.extend([match.strip() for match in matches if match.strip()])
        
        return action_items[:3]  # Limit to top 3
    
    def _summarize_attachments(self, attachments: List[Dict]) -> str:
        """Create a summary of attachments"""
        if not attachments:
            return "No attachments"
        
        count = len(attachments)
        types = set()
        total_size = 0
        
        for att in attachments:
            filename = att.get('filename', '')
            if filename:
                ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                types.add(ext)
            total_size += att.get('size', 0)
        
        size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
        
        return f"{count} attachment{'s' if count > 1 else ''} " \
               f"({', '.join(sorted(types))}) - {size_mb:.1f} MB total"
    
    def _identify_priority_indicators(self, subject: str, body: str) -> List[str]:
        """Identify priority indicators in the email"""
        indicators = []
        content = f"{subject} {body}".lower()
        
        priority_keywords = {
            'high': ['urgent', 'asap', 'immediate', 'critical', 'emergency', 'high priority'],
            'medium': ['important', 'soon', 'reminder', 'follow up'],
            'deadline': ['deadline', 'due date', 'expires', 'by end of day', 'eod'],
        }
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in content for keyword in keywords):
                indicators.append(priority)
        
        return indicators
    
    def extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from arbitrary text using AI or regex fallback"""
        if self.use_ai and self.ai_extractor:
            try:
                return self.ai_extractor.extract_entities_from_text(text)
            except Exception as e:
                logger.warning(f"AI entity extraction failed, using regex fallback: {e}")
        
        # Fallback to regex patterns
        return self._extract_entities(text)