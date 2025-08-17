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
    
    def extract_structured_data(self, subject: str, body: str, sender: str = "", recipients: List[str] = None) -> EmailStructuredData:
        """Extract structured data from email content using AI"""
        if not self.available:
            return self._fallback_extraction(subject, body, sender, recipients or [])
        
        try:
            # Combine email content for analysis
            full_content = f"""
            Subject: {subject}
            From: {sender}
            To: {', '.join(recipients or [])}
            
            Body:
            {body}
            """
            
            # Define extraction prompt
            extraction_prompt = """
            Extract structured information from this email content. Focus on:
            
            1. Summary: A concise 1-2 sentence summary of the email's main purpose
            2. Key Points: Important information, decisions, or topics discussed
            3. Action Items: Specific tasks, requests, or actions that need to be taken
            4. People Mentioned: Names and roles of people referenced (excluding sender/recipients)
            5. Dates: Any dates, deadlines, or time references mentioned
            6. Monetary Amounts: Financial figures, costs, budgets mentioned
            7. Meeting Details: If this is about a meeting (time, location, agenda items)
            8. Contact Information: Phone numbers, addresses, or other contact details
            9. Categories: What type of email this is (meeting, invoice, report, etc.)
            10. Priority Level: high, medium, or low based on language and urgency indicators
            11. Sentiment: positive, neutral, or negative tone of the email
            12. Named Entities: Organizations, locations, products, services mentioned
            
            Return structured data with clear categorization.
            """
            
            # Create example for LangExtract
            example_text = """
                    Subject: Urgent: Budget Review Meeting Tomorrow
                    From: manager@company.com
                    To: team@company.com
                    
                    Body:
                    Hi team,
                    
                    We need to meet tomorrow at 2 PM in Conference Room A to review the Q4 budget.
                    Please bring your department's spending reports. The deadline for budget submission is December 15th, 2024.
                    Contact Sarah at 555-123-4567 if you have questions.
                    
                    Thanks,
                    Mike
                    """
            
            examples = [
                lx.data.ExampleData(
                    text=example_text,
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="summary",
                            extraction_text="Team meeting scheduled for tomorrow at 2 PM to review Q4 budget with spending reports required.",
                            attributes={}
                        ),
                        lx.data.Extraction(
                            extraction_class="categories",
                            extraction_text="meeting",
                            attributes={"type": "business"}
                        ),
                        lx.data.Extraction(
                            extraction_class="priority_level",
                            extraction_text="high",
                            attributes={"reason": "urgent keyword"}
                        ),
                        lx.data.Extraction(
                            extraction_class="people_mentioned",
                            extraction_text="Sarah",
                            attributes={"role": "contact person"}
                        ),
                        lx.data.Extraction(
                            extraction_class="dates_mentioned",
                            extraction_text="December 15th, 2024",
                            attributes={"context": "budget submission deadline"}
                        ),
                        lx.data.Extraction(
                            extraction_class="meeting_details",
                            extraction_text="2 PM tomorrow in Conference Room A",
                            attributes={"purpose": "budget review"}
                        )
                    ]
                )
            ]
            
            # Use LangExtract for structured extraction
            result = lx.extract(
                text_or_documents=full_content,
                prompt_description=extraction_prompt,
                examples=examples,
                model_id=self.model_id
            )
            
            # Process and structure the results
            return self._process_langextract_results(result, subject, body)
            
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return self._fallback_extraction(subject, body, sender, recipients or [])
    
    def _process_langextract_results(self, result, subject: str, body: str) -> EmailStructuredData:
        """Process LangExtract results into structured format"""
        try:
            # Extract structured data from LangExtract result
            extracted = result.extractions if hasattr(result, 'extractions') else []
            
            # Initialize default values
            summary = subject  # Fallback to subject if no AI summary
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
            
            # Process extractions
            for extraction in extracted:
                if hasattr(extraction, 'data') and extraction.data:
                    data = extraction.data
                    
                    # Map extracted data to our structure
                    if 'summary' in data:
                        summary = data['summary']
                    if 'key_points' in data:
                        key_points = data['key_points'] if isinstance(data['key_points'], list) else [data['key_points']]
                    if 'action_items' in data:
                        action_items = self._format_action_items(data['action_items'])
                    if 'people_mentioned' in data:
                        people_mentioned = self._format_people(data['people_mentioned'])
                    if 'dates' in data:
                        dates_mentioned = self._format_dates(data['dates'])
                    if 'monetary_amounts' in data:
                        monetary_amounts = self._format_money(data['monetary_amounts'])
                    if 'meeting_details' in data:
                        meeting_details = data['meeting_details']
                    if 'contact_information' in data:
                        contact_information = self._format_contacts(data['contact_information'])
                    if 'categories' in data:
                        categories = data['categories'] if isinstance(data['categories'], list) else [data['categories']]
                    if 'priority_level' in data:
                        priority_level = data['priority_level'].lower() if data['priority_level'] else "medium"
                    if 'sentiment' in data:
                        sentiment = data['sentiment'].lower() if data['sentiment'] else "neutral"
                    if 'entities' in data:
                        entities = data['entities'] if isinstance(data['entities'], dict) else {}
            
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
            return self._fallback_extraction(subject, body, "", [])
    
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
    
    def _fallback_extraction(self, subject: str, body: str, sender: str, recipients: List[str]) -> EmailStructuredData:
        """Fallback extraction using basic patterns when AI is not available"""
        import re
        
        # Basic regex patterns for fallback
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        money_pattern = r'(?:\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?))'
        
        content = f"{subject} {body}"
        
        # Extract entities using regex
        entities = {
            'emails': re.findall(email_pattern, content),
            'phones': re.findall(phone_pattern, content),
            'dates': re.findall(date_pattern, content),
            'money': re.findall(money_pattern, content, re.IGNORECASE)
        }
        
        # Basic categorization
        content_lower = content.lower()
        categories = []
        if any(word in content_lower for word in ['meeting', 'conference', 'call']):
            categories.append('meeting')
        if any(word in content_lower for word in ['invoice', 'bill', 'payment']):
            categories.append('invoice')
        if any(word in content_lower for word in ['urgent', 'asap', 'critical']):
            categories.append('urgent')
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