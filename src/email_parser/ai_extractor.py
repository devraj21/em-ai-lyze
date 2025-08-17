"""
AI-powered email content extraction using LangExtract
This module provides enhanced entity extraction and content analysis using LLMs.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import langextract as lx
except ImportError:
    print("Warning: langextract not installed. " +
          "Install with: uv pip install 'email-parsing-mcp[ai]'")
    lx = None

logger = logging.getLogger(__name__)


@dataclass
class EmailStructuredData:
    """Structured data extracted from email content using AI"""
    summary: str
    key_points: List[str]
    action_items: List[Dict[str, Any]]
    people_mentioned: List[Dict[str, str]]
    dates_mentioned: List[Dict[str, str]]
    monetary_amounts: List[Dict[str, str]]
    meeting_details: Optional[Dict[str, Any]]
    contact_information: List[Dict[str, str]]
    categories: List[str]
    priority_level: str
    sentiment: str
    entities: Dict[str, List[str]]


class AIEmailExtractor:
    """AI-powered email content extractor using LangExtract"""
    
    def __init__(self, model_id: str = "gemini-1.5-flash", use_local: bool = False):
        self.model_id = model_id
        self.use_local = use_local
        self.available = lx is not None
        
        # Auto-detect local Ollama models if requested
        if use_local and self.available:
            self.model_id = self._detect_ollama_model() or model_id
            logger.info(f"Using local model: {self.model_id}")
        
        if not self.available:
            logger.warning("LangExtract not available. Falling back to regex patterns.")
    
    def _detect_ollama_model(self) -> Optional[str]:
        """Detect available Ollama models on the system"""
        try:
            import subprocess
            
            # Try to get list of available models from Ollama
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header line
                    # Get first model name (most recently pulled)
                    first_model_line = lines[1]
                    model_name = first_model_line.split()[0]
                    logger.info(f"Detected Ollama model: {model_name}")
                    return model_name
            
            logger.warning("No Ollama models found or Ollama not available")
            return None
            
        except Exception as e:
            logger.warning(f"Could not detect Ollama models: {e}")
            # Try common model names as fallback
            common_models = [
                "llama3.2:latest",
                "llama3.2:1b", 
                "llama3.1:latest",
                "llama2:latest",
                "mistral:latest",
                "phi3:latest",
                "gemma:latest"
            ]
            
            for model in common_models:
                try:
                    # Test if model exists
                    test_result = subprocess.run(
                        ["ollama", "show", model],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if test_result.returncode == 0:
                        logger.info(f"Found common Ollama model: {model}")
                        return model
                except:
                    continue
            
            return None
    
    def extract_structured_data(self, subject: str, body: str, sender: str = "", recipients: Optional[List[str]] = None, attachments: Optional[List[Dict]] = None, rag_context=None) -> EmailStructuredData:
        """Extract structured data from email content using AI with comprehensive integration"""
        if not self.available:
            return self._fallback_extraction(subject, body, sender, recipients or [], attachments or [])
        
        try:
            # Prepare attachment information for analysis
            attachment_summary = ""
            if attachments:
                att_details = []
                for att in attachments:
                    filename = att.get('filename', 'unnamed')
                    file_category = att.get('file_category', 'unknown')
                    content_preview = att.get('content_preview', '')
                    content_summary = att.get('content_summary', '')
                    
                    att_detail = f"- {filename} ({file_category})"
                    if content_summary:
                        att_detail += f": {content_summary}"
                    elif content_preview:
                        att_detail += f": {content_preview[:100]}..."
                    att_details.append(att_detail)
                
                attachment_summary = f"""
                
                Attachments ({len(attachments)} files):
                {chr(10).join(att_details)}
                """
            
            # Combine all email components for comprehensive analysis
            full_content = f"""
            Subject: {subject}
            From: {sender}
            To: {', '.join(recipients or [])}
            
            Body:
            {body}
            {attachment_summary}
            """
            
            # Enhanced extraction prompt with RAG context integration
            rag_context_info = ""
            if rag_context and hasattr(rag_context, 'similar_emails') and rag_context.similar_emails:
                similar_subjects = [email.subject for email in rag_context.similar_emails[:3]]
                rag_context_info = f"""
                
                HISTORICAL CONTEXT (from similar emails):
                - {len(rag_context.similar_emails)} similar emails found
                - Similar subjects: {'; '.join(similar_subjects)}
                - Context: {rag_context.context_summary}
                - Suggested categories: {', '.join(rag_context.suggested_categories[:5])}
                - Confidence: {rag_context.confidence_score:.2f}
                
                Use this historical context to inform your analysis, especially for:
                - More accurate categorization based on similar emails
                - Better priority assessment using historical patterns
                - Enhanced entity recognition using domain knowledge
                - Improved sentiment analysis based on organizational context
                """
            
            extraction_prompt = f"""
            Extract structured information from this complete email (subject + body + attachments). 
            Consider ALL components together for context and correlation. Focus on:
            
            1. Summary: A comprehensive 2-3 sentence summary covering the main purpose and key components
            2. Key Points: Important information from subject, body, and attachment content
            3. Action Items: Tasks, requests, or actions from any component (mark source if from attachment)
            4. People Mentioned: Names and roles from all sources (email content and attachments)
            5. Dates: Deadlines, meetings, or time references from all components
            6. Monetary Amounts: Financial figures from email or attachment content
            7. Meeting Details: Meeting information from any source (email or attachments)
            8. Contact Information: Phone numbers, addresses from all sources
            9. Categories: Email type based on complete content analysis (consider attachment types and historical context)
            10. Priority Level: Urgency based on subject, body language, attachment importance, and similar email patterns
            11. Sentiment: Overall tone considering all components and organizational context
            12. Named Entities: Organizations, locations, products from all sources
            13. Content Correlation: How well the subject, body, and attachments align in topic and purpose
            
            Pay special attention to:
            - Cross-references between email content and attachments
            - Consistency of information across all components
            - Additional context provided by attachments
            - Integration of attachment content with email message
            - Historical patterns and context from similar emails
            {rag_context_info}
            
            Return comprehensive structured data reflecting the complete email analysis enhanced with historical context.
            """
            
            # Create comprehensive example
            example_text = """
                    Subject: Q4 Budget Review - Action Required
                    From: manager@company.com
                    To: team@company.com
                    
                    Body:
                    Hi team,
                    
                    Please review the attached budget spreadsheet before tomorrow's meeting at 2 PM in Conference Room A.
                    The spreadsheet shows our Q4 spending against targets. Sarah has identified several areas needing attention.
                    Contact her at 555-123-4567 with any questions before the meeting.
                    
                    Meeting agenda:
                    1. Review Q4 actuals vs budget
                    2. Discuss cost overruns in marketing department
                    3. Plan Q1 budget adjustments
                    
                    Thanks,
                    Mike
                    
                    Attachments (2 files):
                    - Q4_Budget_Analysis.xlsx (spreadsheet): Detailed budget breakdown showing $50K marketing overspend
                    - Meeting_Agenda_Draft.docx (document): Formal agenda with time allocations and discussion points
                    """
            
            examples = [
                lx.data.ExampleData(
                    text=example_text,
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="summary",
                            extraction_text="Budget review meeting scheduled for tomorrow to discuss Q4 spending analysis, with focus on marketing department cost overruns identified in attached spreadsheet.",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="categories",
                            extraction_text="meeting, financial_review, budget",
                            attributes={"has_attachments": True, "attachment_types": ["spreadsheet", "document"]}
                        ),
                        lx.data.Extraction(
                            extraction_class="priority_level",
                            extraction_text="high",
                            attributes={"reason": "action required, budget issues, upcoming deadline"}
                        ),
                        lx.data.Extraction(
                            extraction_class="key_points",
                            extraction_text="Q4 spending exceeded targets, Marketing department cost overruns identified, Budget spreadsheet requires review before meeting",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="action_items",
                            extraction_text="Review budget spreadsheet before meeting, Attend meeting tomorrow at 2 PM",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="monetary_amounts",
                            extraction_text="$50K marketing overspend",
                            attributes={"source": "attachment", "context": "budget_overrun"}
                        ),
                        lx.data.Extraction(
                            extraction_class="content_correlation",
                            extraction_text="High correlation - email explains meeting purpose, attachments provide supporting data and formal agenda",
                            attributes={"score": "0.9"}
                        )
                    ]
                )
            ]
            
            # Use LangExtract for comprehensive extraction
            result = lx.extract(
                text_or_documents=full_content,
                prompt_description=extraction_prompt,
                examples=examples,
                model_id=self.model_id
            )
            
            # Process and structure the results
            return self._process_langextract_results(result, subject, body)
            
        except Exception as e:
            logger.error(f"Error in comprehensive AI extraction: {e}")
            return self._fallback_extraction(subject, body, sender, recipients or [], attachments or [])
    
    def _process_langextract_results(self, result, subject: str, body: str) -> EmailStructuredData:
        """Process LangExtract results into structured format with robust error handling"""
        try:
            # Initialize default values with validation
            summary = self._validate_text(subject, max_length=200) or "No summary available"
            key_points = []
            action_items = []
            people_mentioned = []
            dates_mentioned = []
            monetary_amounts = []
            meeting_details = None
            contact_information = []
            categories = ["general"]
            priority_level = "medium"
            sentiment = "neutral"
            entities = {}
            
            # Safely extract data from LangExtract result
            extracted_data = self._safely_extract_data(result)
            
            if extracted_data:
                # Process each field with validation and fallback
                summary = self._validate_text(
                    extracted_data.get('summary', summary),
                    max_length=500,
                    fallback=summary
                )
                
                key_points = self._validate_list(
                    extracted_data.get('key_points', []),
                    max_items=10,
                    item_validator=lambda x: self._validate_text(x, max_length=200)
                )
                
                action_items = self._format_and_validate_action_items(
                    extracted_data.get('action_items', [])
                )
                
                people_mentioned = self._format_and_validate_people(
                    extracted_data.get('people_mentioned', [])
                )
                
                dates_mentioned = self._format_and_validate_dates(
                    extracted_data.get('dates_mentioned', []) or extracted_data.get('dates', [])
                )
                
                monetary_amounts = self._format_and_validate_money(
                    extracted_data.get('monetary_amounts', []) or extracted_data.get('money', [])
                )
                
                meeting_details = self._validate_meeting_details(
                    extracted_data.get('meeting_details')
                )
                
                contact_information = self._format_and_validate_contacts(
                    extracted_data.get('contact_information', [])
                )
                
                categories = self._validate_categories(
                    extracted_data.get('categories', ["general"])
                )
                
                priority_level = self._validate_priority(
                    extracted_data.get('priority_level', "medium")
                )
                
                sentiment = self._validate_sentiment(
                    extracted_data.get('sentiment', "neutral")
                )
                
                entities = self._validate_entities(
                    extracted_data.get('entities', {})
                )
            
            return EmailStructuredData(
                summary=summary,
                key_points=key_points,
                action_items=action_items,
                people_mentioned=people_mentioned,
                dates_mentioned=dates_mentioned,
                monetary_amounts=monetary_amounts,
                meeting_details=meeting_details,
                contact_information=contact_information,
                categories=categories,
                priority_level=priority_level,
                sentiment=sentiment,
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"Error processing LangExtract results: {e}")
            return self._fallback_extraction(subject, body, "", [], [])
    
    def _safely_extract_data(self, result) -> Dict:
        """Safely extract data from LangExtract result with multiple fallback strategies"""
        extracted_data = {}
        
        try:
            # Strategy 1: Direct extraction from result.extractions
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    if hasattr(extraction, 'data') and extraction.data:
                        if isinstance(extraction.data, dict):
                            extracted_data.update(extraction.data)
                        else:
                            # Try to parse text-based data
                            self._parse_text_extraction(extraction, extracted_data)
                    elif hasattr(extraction, 'extraction_text'):
                        # Parse individual extraction text
                        self._parse_extraction_text(extraction, extracted_data)
            
            # Strategy 2: Direct data access from result
            if hasattr(result, 'data') and isinstance(result.data, dict):
                extracted_data.update(result.data)
            
            # Strategy 3: Parse result as structured text
            if not extracted_data and hasattr(result, '__dict__'):
                for key, value in result.__dict__.items():
                    if key not in ['extractions', 'metadata'] and value:
                        extracted_data[key] = value
            
        except Exception as e:
            logger.warning(f"Error in safe data extraction: {e}")
        
        return extracted_data
    
    def _parse_text_extraction(self, extraction, data_dict: Dict):
        """Parse text-based extraction into structured data"""
        try:
            if hasattr(extraction, 'extraction_class') and hasattr(extraction, 'extraction_text'):
                class_name = str(extraction.extraction_class).lower()
                text_value = str(extraction.extraction_text)
                
                if class_name in ['summary']:
                    data_dict['summary'] = text_value
                elif class_name in ['categories', 'category']:
                    data_dict['categories'] = [text_value] if isinstance(text_value, str) else text_value
                elif class_name in ['priority', 'priority_level']:
                    data_dict['priority_level'] = text_value
                elif class_name in ['sentiment']:
                    data_dict['sentiment'] = text_value
                elif class_name in ['people', 'people_mentioned']:
                    if 'people_mentioned' not in data_dict:
                        data_dict['people_mentioned'] = []
                    data_dict['people_mentioned'].append(text_value)
                elif class_name in ['dates', 'dates_mentioned']:
                    if 'dates_mentioned' not in data_dict:
                        data_dict['dates_mentioned'] = []
                    data_dict['dates_mentioned'].append(text_value)
                
        except Exception as e:
            logger.warning(f"Error parsing text extraction: {e}")
    
    def _parse_extraction_text(self, extraction, data_dict: Dict):
        """Parse extraction text for structured information"""
        try:
            text = str(extraction.extraction_text) if hasattr(extraction, 'extraction_text') else ""
            if not text:
                return
            
            # Simple pattern matching for common structures
            text_lower = text.lower()
            
            # Look for sentiment indicators
            if any(word in text_lower for word in ['positive', 'negative', 'neutral', 'happy', 'angry', 'sad']):
                if 'positive' in text_lower or 'happy' in text_lower:
                    data_dict['sentiment'] = 'positive'
                elif 'negative' in text_lower or 'angry' in text_lower or 'sad' in text_lower:
                    data_dict['sentiment'] = 'negative'
                else:
                    data_dict['sentiment'] = 'neutral'
            
            # Look for priority indicators
            if any(word in text_lower for word in ['high', 'urgent', 'low', 'medium', 'critical']):
                if 'high' in text_lower or 'urgent' in text_lower or 'critical' in text_lower:
                    data_dict['priority_level'] = 'high'
                elif 'low' in text_lower:
                    data_dict['priority_level'] = 'low'
                else:
                    data_dict['priority_level'] = 'medium'
                    
        except Exception as e:
            logger.warning(f"Error parsing extraction text: {e}")
    
    def _validate_text(self, text, max_length: int = 1000, fallback: str = "") -> str:
        """Validate and clean text data"""
        if not text or not isinstance(text, str):
            return fallback
        
        cleaned = text.strip()
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length-3] + "..."
        
        return cleaned if cleaned else fallback
    
    def _validate_list(self, items, max_items: int = 20, item_validator=None) -> List:
        """Validate and clean list data"""
        if not items or not isinstance(items, (list, tuple)):
            return []
        
        validated = []
        for item in items[:max_items]:  # Limit list size
            if item_validator:
                validated_item = item_validator(item)
                if validated_item:
                    validated.append(validated_item)
            else:
                validated.append(item)
        
        return validated
    
    def _format_and_validate_action_items(self, items) -> List[Dict[str, Any]]:
        """Format and validate action items with enhanced error handling"""
        if not items:
            return []
        
        formatted = []
        items_list = items if isinstance(items, list) else [items]
        
        for item in items_list[:10]:  # Limit to 10 items
            try:
                if isinstance(item, str):
                    task_text = self._validate_text(item, max_length=200)
                    if task_text:
                        formatted.append({
                            "task": task_text, 
                            "priority": "medium", 
                            "assigned_to": None
                        })
                elif isinstance(item, dict):
                    validated_item = {
                        "task": self._validate_text(item.get('task', ''), max_length=200),
                        "priority": self._validate_priority(item.get('priority', 'medium')),
                        "assigned_to": self._validate_text(item.get('assigned_to', ''), max_length=100) or None
                    }
                    if validated_item["task"]:
                        formatted.append(validated_item)
            except Exception as e:
                logger.warning(f"Error validating action item: {e}")
                continue
        
        return formatted
    
    def _format_and_validate_people(self, people) -> List[Dict[str, str]]:
        """Format and validate people mentions with enhanced error handling"""
        if not people:
            return []
        
        formatted = []
        people_list = people if isinstance(people, list) else [people]
        
        for person in people_list[:20]:  # Limit to 20 people
            try:
                if isinstance(person, str):
                    name = self._validate_text(person, max_length=100)
                    if name:
                        formatted.append({"name": name, "role": "unknown"})
                elif isinstance(person, dict):
                    name = self._validate_text(person.get('name', ''), max_length=100)
                    role = self._validate_text(person.get('role', 'unknown'), max_length=100)
                    if name:
                        formatted.append({"name": name, "role": role})
            except Exception as e:
                logger.warning(f"Error validating person: {e}")
                continue
        
        return formatted
    
    def _format_and_validate_dates(self, dates) -> List[Dict[str, str]]:
        """Format and validate date mentions with enhanced error handling"""
        if not dates:
            return []
        
        formatted = []
        dates_list = dates if isinstance(dates, list) else [dates]
        
        for date in dates_list[:10]:  # Limit to 10 dates
            try:
                if isinstance(date, str):
                    date_text = self._validate_text(date, max_length=100)
                    if date_text:
                        formatted.append({"date": date_text, "context": "mentioned"})
                elif isinstance(date, dict):
                    date_text = self._validate_text(date.get('date', ''), max_length=100)
                    context = self._validate_text(date.get('context', 'mentioned'), max_length=100)
                    if date_text:
                        formatted.append({"date": date_text, "context": context})
            except Exception as e:
                logger.warning(f"Error validating date: {e}")
                continue
        
        return formatted
    
    def _format_and_validate_money(self, amounts) -> List[Dict[str, str]]:
        """Format and validate monetary amounts with enhanced error handling"""
        if not amounts:
            return []
        
        formatted = []
        amounts_list = amounts if isinstance(amounts, list) else [amounts]
        
        for amount in amounts_list[:10]:  # Limit to 10 amounts
            try:
                if isinstance(amount, str):
                    amount_text = self._validate_text(amount, max_length=50)
                    if amount_text:
                        formatted.append({"amount": amount_text, "context": "mentioned"})
                elif isinstance(amount, dict):
                    amount_text = self._validate_text(amount.get('amount', ''), max_length=50)
                    context = self._validate_text(amount.get('context', 'mentioned'), max_length=100)
                    if amount_text:
                        formatted.append({"amount": amount_text, "context": context})
            except Exception as e:
                logger.warning(f"Error validating amount: {e}")
                continue
        
        return formatted
    
    def _format_and_validate_contacts(self, contacts) -> List[Dict[str, str]]:
        """Format and validate contact information with enhanced error handling"""
        if not contacts:
            return []
        
        formatted = []
        contacts_list = contacts if isinstance(contacts, list) else [contacts]
        
        for contact in contacts_list[:10]:  # Limit to 10 contacts
            try:
                if isinstance(contact, str):
                    contact_text = self._validate_text(contact, max_length=100)
                    if contact_text:
                        contact_type = "email" if "@" in contact_text else "phone" if any(c.isdigit() for c in contact_text) else "other"
                        formatted.append({"value": contact_text, "type": contact_type})
                elif isinstance(contact, dict):
                    value = self._validate_text(contact.get('value', ''), max_length=100)
                    contact_type = self._validate_text(contact.get('type', 'other'), max_length=20)
                    if value:
                        formatted.append({"value": value, "type": contact_type})
            except Exception as e:
                logger.warning(f"Error validating contact: {e}")
                continue
        
        return formatted
    
    def _validate_meeting_details(self, meeting_details) -> Optional[Dict[str, Any]]:
        """Validate meeting details structure"""
        if not meeting_details or not isinstance(meeting_details, dict):
            return None
        
        try:
            validated = {}
            if 'time' in meeting_details:
                validated['time'] = self._validate_text(meeting_details['time'], max_length=100)
            if 'location' in meeting_details:
                validated['location'] = self._validate_text(meeting_details['location'], max_length=200)
            if 'agenda' in meeting_details:
                validated['agenda'] = self._validate_text(meeting_details['agenda'], max_length=500)
            if 'attendees' in meeting_details:
                attendees = meeting_details['attendees']
                if isinstance(attendees, list):
                    validated['attendees'] = [self._validate_text(str(a), max_length=100) for a in attendees[:20]]
            
            return validated if validated else None
            
        except Exception as e:
            logger.warning(f"Error validating meeting details: {e}")
            return None
    
    def _validate_categories(self, categories) -> List[str]:
        """Validate email categories"""
        if not categories:
            return ["general"]
        
        valid_categories = []
        categories_list = categories if isinstance(categories, list) else [categories]
        
        for category in categories_list[:10]:  # Limit to 10 categories
            if isinstance(category, str):
                clean_category = category.lower().strip()
                if clean_category and len(clean_category) <= 50:
                    valid_categories.append(clean_category)
        
        return valid_categories if valid_categories else ["general"]
    
    def _validate_priority(self, priority) -> str:
        """Validate priority level"""
        if not priority or not isinstance(priority, str):
            return "medium"
        
        priority_lower = priority.lower().strip()
        valid_priorities = ["low", "medium", "high", "urgent", "critical"]
        
        # Map common variations
        priority_mapping = {
            "low": "low",
            "medium": "medium", "med": "medium", "normal": "medium",
            "high": "high",
            "urgent": "high", "critical": "high", "important": "high"
        }
        
        return priority_mapping.get(priority_lower, "medium")
    
    def _validate_sentiment(self, sentiment) -> str:
        """Validate sentiment value"""
        if not sentiment or not isinstance(sentiment, str):
            return "neutral"
        
        sentiment_lower = sentiment.lower().strip()
        valid_sentiments = ["positive", "negative", "neutral"]
        
        # Map common variations
        sentiment_mapping = {
            "positive": "positive", "pos": "positive", "good": "positive", "happy": "positive",
            "negative": "negative", "neg": "negative", "bad": "negative", "angry": "negative", "sad": "negative",
            "neutral": "neutral", "normal": "neutral", "okay": "neutral", "ok": "neutral"
        }
        
        return sentiment_mapping.get(sentiment_lower, "neutral")
    
    def _validate_entities(self, entities) -> Dict[str, List[str]]:
        """Validate entities dictionary"""
        if not entities or not isinstance(entities, dict):
            return {}
        
        validated = {}
        for key, values in entities.items():
            if isinstance(key, str) and key.strip():
                clean_key = key.strip().lower()
                if isinstance(values, list):
                    clean_values = [self._validate_text(str(v), max_length=100) for v in values[:20] if v]
                    validated[clean_key] = [v for v in clean_values if v]
                elif isinstance(values, str) and values.strip():
                    validated[clean_key] = [self._validate_text(values, max_length=100)]
        
        return validated
    
    def _format_action_items(self, items) -> List[Dict[str, Any]]:
        """Format action items with structure"""
        if not items:
            return []
        
        formatted = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    formatted.append({"task": item, "priority": "medium", "assigned_to": None})
                elif isinstance(item, dict):
                    formatted.append(item)
        elif isinstance(items, str):
            formatted.append({"task": items, "priority": "medium", "assigned_to": None})
        
        return formatted
    
    def _format_people(self, people) -> List[Dict[str, str]]:
        """Format people mentions with structure"""
        if not people:
            return []
        
        formatted = []
        if isinstance(people, list):
            for person in people:
                if isinstance(person, str):
                    formatted.append({"name": person, "role": "unknown"})
                elif isinstance(person, dict):
                    formatted.append(person)
        elif isinstance(people, str):
            formatted.append({"name": people, "role": "unknown"})
        
        return formatted
    
    def _format_dates(self, dates) -> List[Dict[str, str]]:
        """Format date mentions with context"""
        if not dates:
            return []
        
        formatted = []
        if isinstance(dates, list):
            for date in dates:
                if isinstance(date, str):
                    formatted.append({"date": date, "context": "mentioned"})
                elif isinstance(date, dict):
                    formatted.append(date)
        elif isinstance(dates, str):
            formatted.append({"date": dates, "context": "mentioned"})
        
        return formatted
    
    def _format_money(self, amounts) -> List[Dict[str, str]]:
        """Format monetary amounts with context"""
        if not amounts:
            return []
        
        formatted = []
        if isinstance(amounts, list):
            for amount in amounts:
                if isinstance(amount, str):
                    formatted.append({"amount": amount, "context": "mentioned"})
                elif isinstance(amount, dict):
                    formatted.append(amount)
        elif isinstance(amounts, str):
            formatted.append({"amount": amounts, "context": "mentioned"})
        
        return formatted
    
    def _format_contacts(self, contacts) -> List[Dict[str, str]]:
        """Format contact information with type"""
        if not contacts:
            return []
        
        formatted = []
        if isinstance(contacts, list):
            for contact in contacts:
                if isinstance(contact, str):
                    contact_type = "email" if "@" in contact else "phone" if any(c.isdigit() for c in contact) else "other"
                    formatted.append({"value": contact, "type": contact_type})
                elif isinstance(contact, dict):
                    formatted.append(contact)
        elif isinstance(contacts, str):
            contact_type = "email" if "@" in contacts else "phone" if any(c.isdigit() for c in contacts) else "other"
            formatted.append({"value": contacts, "type": contact_type})
        
        return formatted
    
    def _fallback_extraction(self, subject: str, body: str, sender: str, recipients: List[str], attachments: Optional[List[Dict]] = None) -> EmailStructuredData:
        """Fallback extraction using basic patterns when AI is not available"""
        import re
        
        # Basic regex patterns for fallback
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        money_pattern = r'(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?))'
        
        content = f"{subject} {body}"
        
        # Include attachment content if available
        if attachments:
            for att in attachments:
                extracted_text = att.get('extracted_text', '')
                if extracted_text:
                    content += f" {extracted_text}"
        
        # Extract entities using regex
        entities = {
            'emails': re.findall(email_pattern, content),
            'phones': re.findall(phone_pattern, content),
            'dates': re.findall(date_pattern, content),
            'money': re.findall(money_pattern, content, re.IGNORECASE)
        }
        
        # Enhanced categorization with attachment consideration
        content_lower = content.lower()
        categories = []
        
        # Text-based categories
        if any(word in content_lower for word in ['meeting', 'conference', 'call', 'appointment']):
            categories.append('meeting')
        if any(word in content_lower for word in ['invoice', 'bill', 'payment', 'receipt']):
            categories.append('invoice')
        if any(word in content_lower for word in ['urgent', 'asap', 'critical', 'immediate']):
            categories.append('urgent')
        if any(word in content_lower for word in ['report', 'analysis', 'summary', 'findings']):
            categories.append('report')
        if any(word in content_lower for word in ['contract', 'agreement', 'legal', 'terms']):
            categories.append('contract')
        
        # Attachment-based categories
        if attachments:
            categories.append('has_attachments')
            file_categories = [att.get('file_category', '') for att in attachments]
            
            if 'document' in file_categories:
                categories.append('document')
            if 'spreadsheet' in file_categories:
                categories.append('data_analysis')
            if 'image' in file_categories:
                categories.append('media')
            if 'presentation' in file_categories:
                categories.append('presentation')
        
        if not categories:
            categories = ['general']
        
        # Basic priority detection
        priority_level = "high" if any(word in content_lower for word in ['urgent', 'asap', 'critical', 'emergency']) else "medium"
        
        # Basic summary (first sentence of body)
        sentences = re.split(r'[.!?]+', body.strip())
        summary = sentences[0].strip() if sentences and sentences[0].strip() else subject
        if len(summary) > 100:
            summary = summary[:97] + "..."
        
        return EmailStructuredData(
            summary=summary,
            key_points=[],
            action_items=[],
            people_mentioned=[],
            dates_mentioned=[{"date": date, "context": "mentioned"} for date in entities['dates']],
            monetary_amounts=[{"amount": amount, "context": "mentioned"} for amount in entities['money']],
            meeting_details=None,
            contact_information=[],
            categories=categories,
            priority_level=priority_level,
            sentiment="neutral",
            entities=entities
        )
    
    def extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from arbitrary text using AI"""
        if not self.available:
            return self._fallback_entity_extraction(text)
        
        try:
            entity_prompt = """
            Extract the following entities from this text:
            - People: Names of individuals
            - Organizations: Company names, institutions
            - Locations: Cities, countries, addresses
            - Dates: Any date references
            - Money: Financial amounts
            - Products: Product or service names
            - Events: Meeting names, project names
            
            Return as structured lists for each category.
            """
            
            # Create example for entity extraction
            entity_example_text = "Meeting with John Smith at Microsoft tomorrow at 3 PM. Budget is $50,000 for the Azure project."
            entity_examples = [
                lx.data.ExampleData(
                    text=entity_example_text,
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="people",
                            extraction_text="John Smith",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="organizations",
                            extraction_text="Microsoft",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="dates",
                            extraction_text="tomorrow at 3 PM",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="money",
                            extraction_text="$50,000",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="products",
                            extraction_text="Azure",
                            attributes={}
                        )
                    ]
                )
            ]
            
            result = lx.extract(
                text_or_documents=text,
                prompt_description=entity_prompt,
                examples=entity_examples,
                model_id=self.model_id
            )
            
            # Process results into entity dictionary
            entities = {}
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    if hasattr(extraction, 'data') and extraction.data:
                        entities.update(extraction.data)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in AI entity extraction: {e}")
            return self._fallback_entity_extraction(text)
    
    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """Fallback entity extraction using regex patterns"""
        import re
        
        patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'phones': r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'dates': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            'urls': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            'money': r'(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?))',
        }
        
        entities = {}
        for entity_type, pattern in patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities[entity_type] = list(set([match.strip() for match in matches if match.strip()]))
            except Exception as e:
                logger.warning(f"Error in pattern {entity_type}: {e}")
                entities[entity_type] = []
        
        return entities