# Parser API Reference

Complete API documentation for the EmailParser class and related components.

## 📋 Table of Contents

- [EmailParser](#emailparser)
- [EmailContent](#emailcontent)
- [AIEmailExtractor](#aiemailextractor)
- [EmailStructuredData](#emailstructureddata)
- [Usage Examples](#usage-examples)

## EmailParser

Main email parsing class with AI and local model support.

### Constructor

```python
EmailParser(use_ai: bool = True, ai_model: str = "gemini-1.5-flash", use_local: bool = False)
```

**Parameters:**
- `use_ai` (bool): Enable AI-powered extraction. Default: True
- `ai_model` (str): AI model to use. Default: "gemini-1.5-flash"
- `use_local` (bool): Use local Ollama models. Default: False

**Example:**
```python
from email_parser.parser import EmailParser

# Local AI with auto-detected model
parser = EmailParser(use_ai=True, use_local=True)

# Cloud AI with specific model
parser = EmailParser(use_ai=True, ai_model="gemini-1.5-flash")

# Regex-only parsing
parser = EmailParser(use_ai=False)
```

### Methods

#### `parse_msg_file(file_path: Path) -> Optional[EmailContent]`

Parse a .msg email file and extract structured content.

**Parameters:**
- `file_path` (Path): Path to the .msg file

**Returns:**
- `EmailContent`: Structured email data, or None if parsing failed

**Example:**
```python
from pathlib import Path

email_data = parser.parse_msg_file(Path("email.msg"))
if email_data:
    print(f"Subject: {email_data.subject}")
    print(f"AI Summary: {email_data.ai_summary}")
```

#### `extract_entities_from_text(text: str) -> Dict[str, List[str]]`

Extract entities from arbitrary text using AI or regex patterns.

**Parameters:**
- `text` (str): Text content to analyze

**Returns:**
- `Dict[str, List[str]]`: Dictionary mapping entity types to lists of found entities

**Extracted Entity Types:**
- `emails`: Email addresses
- `phones`: Phone numbers
- `dates`: Date references  
- `money`: Monetary amounts
- `urls`: Web URLs
- `people`: Person names (AI only)
- `organizations`: Company/organization names (AI only)
- `locations`: Geographic locations (AI only)
- `events`: Meeting/event names (AI only)

**Example:**
```python
text = "Meeting with John at john@company.com tomorrow at 3 PM about $50k budget"
entities = parser.extract_entities_from_text(text)

print(entities)
# {
#   'emails': ['john@company.com'],
#   'money': ['$50k'],
#   'dates': ['tomorrow at 3 PM'],
#   'people': ['John'],
#   'events': ['Meeting'],
#   '_ai_enhanced': ['true']
# }
```

### Properties

#### `supported_extensions: List[str]`
List of supported file extensions. Currently: `['.msg']`

#### `use_ai: bool`
Whether AI processing is enabled.

#### `use_local: bool` 
Whether local Ollama models are being used.

#### `ai_extractor: Optional[AIEmailExtractor]`
The AI extractor instance, if AI is enabled.

## EmailContent

Structured email content dataclass containing all parsed information.

### Fields

#### Basic Email Data
- `message_id: str` - Unique message identifier
- `subject: str` - Email subject line
- `sender: str` - Sender email address
- `recipients: List[str]` - Primary recipients
- `cc_recipients: List[str]` - CC recipients
- `bcc_recipients: List[str]` - BCC recipients
- `sent_date: Optional[datetime]` - When email was sent

#### Content
- `body_text: str` - Plain text email body
- `body_html: str` - HTML email body
- `attachments: List[Dict[str, Any]]` - Attachment information

#### Analysis Results
- `priority: str` - Email priority from headers
- `categories: List[str]` - Detected email categories
- `correlation_score: float` - Subject-body correlation score (0.0-1.0)
- `extracted_entities: Dict[str, List[str]]` - Extracted entities
- `standardized_format: Dict[str, Any]` - Structured analysis results

#### AI-Enhanced Fields
- `ai_structured_data: Optional[EmailStructuredData]` - Full AI analysis
- `sentiment: str` - Email sentiment (positive/neutral/negative)
- `ai_summary: str` - AI-generated summary
- `ai_priority: str` - AI-detected priority (low/medium/high)

### Usage Example

```python
email_data = parser.parse_msg_file(Path("email.msg"))

# Basic information
print(f"From: {email_data.sender}")
print(f"Subject: {email_data.subject}")
print(f"Date: {email_data.sent_date}")

# AI analysis
print(f"Summary: {email_data.ai_summary}")
print(f"Sentiment: {email_data.sentiment}")
print(f"Priority: {email_data.ai_priority}")

# Entities
for entity_type, values in email_data.extracted_entities.items():
    if values and not entity_type.startswith('_'):
        print(f"{entity_type}: {values}")

# Structured format
action_items = email_data.standardized_format.get('action_items', [])
if action_items:
    print("Action Items:")
    for item in action_items:
        print(f"  - {item}")
```

## AIEmailExtractor

AI-powered email content extraction using LangExtract.

### Constructor

```python
AIEmailExtractor(model_id: str = "gemini-1.5-flash", use_local: bool = False)
```

**Parameters:**
- `model_id` (str): AI model identifier
- `use_local` (bool): Use local Ollama models

### Methods

#### `extract_structured_data(subject: str, body: str, sender: str = "", recipients: List[str] = None) -> EmailStructuredData`

Extract comprehensive structured data from email content.

**Parameters:**
- `subject` (str): Email subject
- `body` (str): Email body text
- `sender` (str): Sender email (optional)
- `recipients` (List[str]): Recipient emails (optional)

**Returns:**
- `EmailStructuredData`: Structured analysis results

#### `extract_entities_from_text(text: str) -> Dict[str, List[str]]`

Extract entities from arbitrary text using AI.

**Parameters:**
- `text` (str): Text to analyze

**Returns:**
- `Dict[str, List[str]]`: Extracted entities by type

## EmailStructuredData

Comprehensive structured data extracted by AI.

### Fields

#### Content Analysis
- `summary: str` - Concise email summary
- `key_points: List[str]` - Important information points
- `sentiment: str` - Email sentiment
- `categories: List[str]` - Email categories
- `priority_level: str` - Priority assessment

#### Extracted Information
- `people_mentioned: List[Dict[str, str]]` - People with roles
- `dates_mentioned: List[Dict[str, str]]` - Dates with context
- `monetary_amounts: List[Dict[str, str]]` - Money with context
- `contact_information: List[Dict[str, str]]` - Contact details
- `entities: Dict[str, List[str]]` - All extracted entities

#### Action Items & Meetings
- `action_items: List[Dict[str, Any]]` - Tasks with priorities
- `meeting_details: Optional[Dict[str, Any]]` - Meeting information

### Example Usage

```python
from email_parser.ai_extractor import AIEmailExtractor

extractor = AIEmailExtractor(use_local=True)

structured_data = extractor.extract_structured_data(
    subject="Budget Meeting Tomorrow",
    body="Hi team, let's meet tomorrow at 2 PM to discuss the $50k budget...",
    sender="manager@company.com",
    recipients=["team@company.com"]
)

print(f"Summary: {structured_data.summary}")
print(f"Priority: {structured_data.priority_level}")
print(f"Action Items: {len(structured_data.action_items)}")

for item in structured_data.action_items:
    print(f"  - {item.get('task', item)}")
```

## Usage Examples

### Basic Email Parsing

```python
from email_parser.parser import EmailParser
from pathlib import Path

# Initialize parser
parser = EmailParser(use_ai=True, use_local=True)

# Parse single email
email_data = parser.parse_msg_file(Path("sample.msg"))

if email_data:
    print(f"📧 {email_data.subject}")
    print(f"👤 From: {email_data.sender}")
    print(f"📝 Summary: {email_data.ai_summary}")
    print(f"😊 Sentiment: {email_data.sentiment}")
    print(f"🎯 Priority: {email_data.ai_priority}")
    print(f"🏷️ Categories: {', '.join(email_data.categories)}")
```

### Batch Processing

```python
from pathlib import Path

def process_email_folder(folder_path):
    parser = EmailParser(use_ai=True, use_local=True)
    folder = Path(folder_path)
    
    results = []
    for msg_file in folder.glob("*.msg"):
        email_data = parser.parse_msg_file(msg_file)
        if email_data:
            results.append({
                'filename': msg_file.name,
                'subject': email_data.subject,
                'sender': email_data.sender,
                'sentiment': email_data.sentiment,
                'categories': email_data.categories,
                'entity_count': sum(len(v) for v in email_data.extracted_entities.values())
            })
    
    return results

# Process folder
results = process_email_folder("./emails")
print(f"Processed {len(results)} emails")
```

### Custom Entity Processing

```python
def extract_meeting_info(text):
    parser = EmailParser(use_ai=True, use_local=True)
    
    # Extract entities
    entities = parser.extract_entities_from_text(text)
    
    # Filter for meeting-related information
    meeting_info = {
        'people': entities.get('people', []),
        'dates': entities.get('dates', []),
        'locations': entities.get('locations', []),
        'events': entities.get('events', [])
    }
    
    return meeting_info

text = "Team meeting with Sarah and John tomorrow at 3 PM in Conference Room B"
meeting_info = extract_meeting_info(text)
print(meeting_info)
```

### Error Handling

```python
from email_parser.parser import EmailParser
from pathlib import Path
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_parse_email(file_path):
    try:
        parser = EmailParser(use_ai=True, use_local=True)
        email_data = parser.parse_msg_file(Path(file_path))
        
        if email_data:
            return {
                'success': True,
                'data': email_data,
                'ai_enhanced': email_data.ai_structured_data is not None
            }
        else:
            return {'success': False, 'error': 'Failed to parse email'}
            
    except FileNotFoundError:
        return {'success': False, 'error': 'File not found'}
    except ImportError as e:
        return {'success': False, 'error': f'Missing dependencies: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}")
        return {'success': False, 'error': str(e)}

# Usage with error handling
result = safe_parse_email("email.msg")
if result['success']:
    print(f"✅ Parsed: {result['data'].subject}")
    print(f"🤖 AI Enhanced: {result['ai_enhanced']}")
else:
    print(f"❌ Error: {result['error']}")
```

## Type Hints

For full type safety, import the types:

```python
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from email_parser.parser import EmailParser, EmailContent
from email_parser.ai_extractor import AIEmailExtractor, EmailStructuredData

def process_email(file_path: Path) -> Optional[EmailContent]:
    parser: EmailParser = EmailParser(use_ai=True, use_local=True)
    return parser.parse_msg_file(file_path)

def extract_entities(text: str) -> Dict[str, List[str]]:
    parser: EmailParser = EmailParser(use_ai=True, use_local=True)
    return parser.extract_entities_from_text(text)
```

---

This API provides comprehensive email parsing capabilities with both traditional and AI-enhanced analysis. Use the examples above to get started with your specific use case!