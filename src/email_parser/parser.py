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

class EmailParser:
    """Main email parsing engine"""
    
    def __init__(self, use_ai: bool = True, ai_model: str = "gemini-1.5-flash", use_local: bool = False):
        self.supported_extensions = ['.msg']
        self.use_ai = use_ai and AI_AVAILABLE
        self.use_local = use_local
        
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
            
            # AI-Enhanced Processing
            ai_structured_data = None
            ai_summary = ""
            ai_priority = "medium"
            sentiment = "neutral"
            
            if self.use_ai and self.ai_extractor:
                try:
                    ai_structured_data = self.ai_extractor.extract_structured_data(
                        subject, body_text, sender, recipients
                    )
                    ai_summary = ai_structured_data.summary
                    ai_priority = ai_structured_data.priority_level
                    sentiment = ai_structured_data.sentiment
                    # Use AI-extracted entities and categories
                    extracted_entities = ai_structured_data.entities
                    categories = ai_structured_data.categories
                    logger.info("Successfully applied AI extraction")
                except Exception as e:
                    logger.warning(f"AI extraction failed, falling back to regex: {e}")
                    # Fallback to traditional extraction
                    combined_text = f"{subject} {body_text}"
                    extracted_entities = self._extract_entities(combined_text)
                    categories = self._categorize_email(subject, body_text, attachments)
            else:
                # Traditional extraction
                combined_text = f"{subject} {body_text}"
                extracted_entities = self._extract_entities(combined_text)
                categories = self._categorize_email(subject, body_text, attachments)
            
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
                ai_priority=ai_priority
            )
            
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
        """Extract attachment information"""
        attachments = []
        
        try:
            for attachment in msg.attachments:
                att_info = {
                    'filename': getattr(attachment, 'longFilename', '') or 
                               getattr(attachment, 'shortFilename', ''),
                    'size': getattr(attachment, 'size', 0),
                    'content_type': getattr(attachment, 'mimetype', ''),
                    'is_embedded': hasattr(attachment, 'cid'),
                }
                attachments.append(att_info)
        except Exception as e:
            logger.warning(f"Error extracting attachments: {e}")
        
        return attachments
    
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
        """Calculate correlation score between subject, body, and attachments"""
        score = 0.0
        
        # Subject-body correlation
        subject_words = set(re.findall(r'\w+', subject.lower()))
        body_words = set(re.findall(r'\w+', body.lower()))
        
        if subject_words and body_words:
            common_words = subject_words.intersection(body_words)
            score += len(common_words) / max(len(subject_words), len(body_words))
        
        # Subject-attachment correlation
        if attachments:
            attachment_names = [att.get('filename', '').lower() for att in attachments]
            for name in attachment_names:
                name_words = set(re.findall(r'\w+', name))
                if name_words and subject_words:
                    common = name_words.intersection(subject_words)
                    score += len(common) / len(subject_words) * 0.5  # Weight attachment correlation less
        
        return min(score, 1.0)  # Cap at 1.0
    
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