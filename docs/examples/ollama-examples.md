# Ollama Examples

Complete examples showing how to use local AI with Ollama for email parsing.

## 🏠 Basic Local AI Setup

### Simple Email Parsing
```python
from email_parser.parser import EmailParser
from pathlib import Path

# Initialize with local AI (auto-detects best model)
parser = EmailParser(use_ai=True, use_local=True)

# Parse an email
email_data = parser.parse_msg_file(Path("sample_email.msg"))

print(f"Subject: {email_data.subject}")
print(f"AI Summary: {email_data.ai_summary}")
print(f"Sentiment: {email_data.sentiment}")
print(f"Priority: {email_data.ai_priority}")
```

### Entity Extraction
```python
from email_parser.parser import EmailParser

parser = EmailParser(use_ai=True, use_local=True)

# Extract from email content
email_text = """
Hi team,

Let's meet tomorrow at 3 PM EST in Conference Room B to discuss 
the $150,000 budget allocation for Q4. 

Contact Sarah Johnson at sarah@company.com or 555-123-4567 
if you can't attend.

Thanks,
Mike Rodriguez
Director of Marketing
"""

entities = parser.extract_entities_from_text(email_text)

print("🔍 Extracted Entities:")
for entity_type, values in entities.items():
    if values and not entity_type.startswith('_'):
        print(f"  • {entity_type.title()}: {values}")

# Output:
# 🔍 Extracted Entities:
#   • People: ['Sarah Johnson', 'Mike Rodriguez']
#   • Emails: ['sarah@company.com']
#   • Phones: ['555-123-4567']
#   • Money: ['$150,000']
#   • Dates: ['tomorrow at 3 PM EST']
#   • Locations: ['Conference Room B']
#   • Events: ['meeting']
```

## 🎯 Model-Specific Examples

### Using Different Ollama Models
```python
from email_parser.parser import EmailParser

# Fast processing with lightweight model
fast_parser = EmailParser(
    use_ai=True, 
    use_local=True, 
    ai_model="llama3.2:1b"
)

# Balanced performance
balanced_parser = EmailParser(
    use_ai=True,
    use_local=True, 
    ai_model="phi3:mini"
)

# Best accuracy
accuracy_parser = EmailParser(
    use_ai=True,
    use_local=True,
    ai_model="mistral:latest"
)

# Test all models on the same text
test_text = "Budget meeting with John tomorrow at 2 PM about $50k project"

print("🏃‍♂️ Fast Model (llama3.2:1b):")
fast_entities = fast_parser.extract_entities_from_text(test_text)
print(f"Entities found: {sum(len(v) for v in fast_entities.values() if not str(v).startswith('_'))}")

print("\n⚖️ Balanced Model (phi3:mini):")
balanced_entities = balanced_parser.extract_entities_from_text(test_text)
print(f"Entities found: {sum(len(v) for v in balanced_entities.values() if not str(v).startswith('_'))}")

print("\n🎯 Accuracy Model (mistral:latest):")
accuracy_entities = accuracy_parser.extract_entities_from_text(test_text)
print(f"Entities found: {sum(len(v) for v in accuracy_entities.values() if not str(v).startswith('_'))}")
```

### Performance Comparison
```python
import time
from email_parser.parser import EmailParser

def benchmark_model(model_name, text):
    parser = EmailParser(use_ai=True, use_local=True, ai_model=model_name)
    
    start_time = time.time()
    entities = parser.extract_entities_from_text(text)
    end_time = time.time()
    
    entity_count = sum(len(v) for v in entities.values() if not str(v).startswith('_'))
    
    return {
        'model': model_name,
        'time': end_time - start_time,
        'entities': entity_count
    }

# Test text
complex_text = """
Subject: Urgent: Q4 Budget Review Meeting

Hi Finance Team,

We need to finalize our Q4 budget by December 15th, 2024. The board meeting
is scheduled for tomorrow at 2:00 PM EST in the main conference room.

Key agenda items:
1. Review $150,000 marketing budget allocation
2. Discuss the new product launch timeline for January 2025
3. Approve additional $75,000 for engineering resources

Please confirm attendance by calling Sarah Johnson at 555-123-4567
or emailing sarah.johnson@company.com.

This is critical for our success in 2025.

Best regards,
Mike Rodriguez
Director of Finance
"""

# Benchmark different models
models = ["llama3.2:1b", "phi3:mini", "mistral:latest"]
results = []

for model in models:
    try:
        result = benchmark_model(model, complex_text)
        results.append(result)
        print(f"✅ {result['model']}: {result['time']:.1f}s, {result['entities']} entities")
    except Exception as e:
        print(f"❌ {model}: {e}")

# Show recommendations
print("\n📊 Recommendations:")
print("• For high-volume processing: llama3.2:1b")
print("• For balanced use: phi3:mini") 
print("• For maximum accuracy: mistral:latest")
```

## 📊 Batch Processing Examples

### Process Email Folder
```python
from email_parser.parser import EmailParser
from pathlib import Path
import json

def process_email_folder(folder_path, model_name="phi3:mini"):
    """Process all .msg files in a folder with local AI"""
    
    parser = EmailParser(use_ai=True, use_local=True, ai_model=model_name)
    folder = Path(folder_path)
    
    # Find all .msg files
    msg_files = list(folder.glob("*.msg"))
    print(f"📁 Found {len(msg_files)} email files")
    
    results = []
    for msg_file in msg_files:
        try:
            email_data = parser.parse_msg_file(msg_file)
            if email_data:
                results.append({
                    'filename': msg_file.name,
                    'subject': email_data.subject,
                    'sender': email_data.sender,
                    'ai_summary': email_data.ai_summary,
                    'sentiment': email_data.sentiment,
                    'priority': email_data.ai_priority,
                    'categories': email_data.categories,
                    'entity_count': sum(len(v) for v in email_data.extracted_entities.values())
                })
                print(f"✅ {msg_file.name}")
            else:
                print(f"❌ Failed: {msg_file.name}")
        except Exception as e:
            print(f"❌ Error {msg_file.name}: {e}")
    
    return results

# Usage
results = process_email_folder("./sample_emails")

# Analyze results
if results:
    print(f"\n📈 Analysis Summary:")
    
    # Sentiment distribution
    sentiments = {}
    for result in results:
        sentiment = result['sentiment']
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
    print(f"Sentiment: {sentiments}")
    
    # Category frequency
    categories = {}
    for result in results:
        for category in result['categories']:
            categories[category] = categories.get(category, 0) + 1
    top_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5])
    print(f"Top Categories: {top_categories}")
    
    # Save results
    with open('email_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Saved analysis to email_analysis.json")
```

### Email Classification Pipeline
```python
from email_parser.parser import EmailParser
from pathlib import Path
import shutil

def classify_emails(input_folder, output_folder, model="phi3:mini"):
    """Automatically classify and organize emails by category"""
    
    parser = EmailParser(use_ai=True, use_local=True, ai_model=model)
    
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Category mappings
    category_folders = {
        'meeting': 'meetings',
        'invoice': 'financial', 
        'report': 'reports',
        'urgent': 'urgent',
        'support': 'support_tickets',
        'contract': 'legal'
    }
    
    # Create category folders
    for folder in category_folders.values():
        (output_path / folder).mkdir(exist_ok=True)
    (output_path / 'other').mkdir(exist_ok=True)
    
    msg_files = list(input_path.glob("*.msg"))
    print(f"🏷️ Classifying {len(msg_files)} emails...")
    
    classification_results = {}
    
    for msg_file in msg_files:
        try:
            email_data = parser.parse_msg_file(msg_file)
            if email_data and email_data.categories:
                # Find best category match
                primary_category = None
                for category in email_data.categories:
                    if category in category_folders:
                        primary_category = category
                        break
                
                # Move file to appropriate folder
                if primary_category:
                    dest_folder = output_path / category_folders[primary_category]
                    dest_file = dest_folder / msg_file.name
                    shutil.copy2(msg_file, dest_file)
                    print(f"📁 {msg_file.name} → {category_folders[primary_category]}")
                    
                    classification_results[msg_file.name] = {
                        'category': primary_category,
                        'sentiment': email_data.sentiment,
                        'priority': email_data.ai_priority,
                        'summary': email_data.ai_summary[:100] + '...'
                    }
                else:
                    # Move to 'other' folder
                    dest_file = output_path / 'other' / msg_file.name
                    shutil.copy2(msg_file, dest_file)
                    print(f"❓ {msg_file.name} → other")
                    
                    classification_results[msg_file.name] = {
                        'category': 'other',
                        'detected_categories': email_data.categories
                    }
        except Exception as e:
            print(f"❌ Error processing {msg_file.name}: {e}")
    
    # Save classification report
    with open(output_path / 'classification_report.json', 'w') as f:
        json.dump(classification_results, f, indent=2)
    
    print(f"✅ Classification complete! Report saved to classification_report.json")
    return classification_results

# Usage
results = classify_emails('./inbox_emails', './organized_emails')
```

## 🔧 MCP Server with Ollama

### Start Local MCP Server
```python
from email_parser.mcp_server import EmailParserMCPServer

# Create server with local AI
server = EmailParserMCPServer(
    name="email-parser-local",
    use_ai=True,
    use_local=True,
    ai_model="phi3:mini"
)

print("🚀 Starting MCP server with local AI...")
print("Connect from Claude Desktop to use email parsing tools!")

# This would start the server (in actual usage)
# server.mcp.run()
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "email-parser-local": {
      "command": "python", 
      "args": ["-m", "src.email_parser.main", "--mcp", "--local", "--model", "phi3:mini"],
      "cwd": "/path/to/email-parser"
    }
  }
}
```

## 🔍 Advanced Entity Extraction

### Custom Entity Processing
```python
from email_parser.ai_extractor import AIEmailExtractor

# Create custom AI extractor
extractor = AIEmailExtractor(
    model_id="mistral:latest",
    use_local=True
)

def extract_meeting_details(text):
    """Extract detailed meeting information"""
    
    # Use the AI extractor directly
    entities = extractor.extract_entities_from_text(text)
    
    # Extract structured data
    structured = extractor.extract_structured_data(
        subject="Meeting Details",
        body=text,
        sender="",
        recipients=[]
    )
    
    # Combine results
    meeting_info = {
        'basic_entities': entities,
        'meeting_details': structured.meeting_details,
        'action_items': structured.action_items,
        'people_mentioned': structured.people_mentioned,
        'dates_mentioned': structured.dates_mentioned
    }
    
    return meeting_info

# Test with meeting text
meeting_text = """
Team Meeting Tomorrow

Hi everyone,

Let's meet tomorrow (December 15th) at 2:00 PM EST in Conference Room B 
on the 3rd floor to discuss:

1. Q4 budget review - Sarah will present the numbers
2. New product launch timeline - John needs to update us on development
3. Holiday schedule planning - Mike will coordinate time off

Please bring:
- Your department's Q4 spending reports
- Ideas for the product marketing campaign
- Your holiday availability calendar

If you can't attend, please let me know by calling 555-123-4567 
or email me at manager@company.com.

Thanks!
Alex Rodriguez
Project Manager
"""

meeting_info = extract_meeting_details(meeting_text)

print("🏢 Meeting Analysis:")
print(f"Basic entities: {meeting_info['basic_entities']}")
print(f"Meeting details: {meeting_info['meeting_details']}")
print(f"Action items: {len(meeting_info['action_items'])}")
print(f"People mentioned: {len(meeting_info['people_mentioned'])}")
```

## 📈 Monitoring & Performance

### Processing Time Analysis
```python
import time
from email_parser.parser import EmailParser
from pathlib import Path

def analyze_processing_performance():
    """Analyze processing performance across different models"""
    
    models = ["llama3.2:1b", "phi3:mini", "mistral:latest"]
    sample_texts = [
        "Quick meeting tomorrow at 2 PM",
        "Budget review meeting with full team next week about $500k allocation",
        """
        Comprehensive quarterly business review scheduled for next Tuesday at 9 AM EST 
        in the main conference room. We'll discuss the $2.5M budget allocation, 
        Q4 performance metrics, and 2025 strategic planning initiatives. 
        Key stakeholders including Sarah Johnson (CFO), Mike Rodriguez (CTO), 
        and Jennifer Smith (VP Marketing) will present their departmental updates.
        """
    ]
    
    results = {}
    
    for model in models:
        print(f"\n🧪 Testing {model}:")
        model_results = []
        
        try:
            parser = EmailParser(use_ai=True, use_local=True, ai_model=model)
            
            for i, text in enumerate(sample_texts, 1):
                start_time = time.time()
                entities = parser.extract_entities_from_text(text)
                end_time = time.time()
                
                processing_time = end_time - start_time
                entity_count = sum(len(v) for v in entities.values() if not str(v).startswith('_'))
                
                model_results.append({
                    'text_length': len(text),
                    'processing_time': processing_time,
                    'entities_found': entity_count,
                    'chars_per_second': len(text) / processing_time
                })
                
                print(f"  Text {i}: {processing_time:.1f}s, {entity_count} entities")
            
            results[model] = model_results
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    for model, model_results in results.items():
        avg_time = sum(r['processing_time'] for r in model_results) / len(model_results)
        avg_entities = sum(r['entities_found'] for r in model_results) / len(model_results)
        avg_speed = sum(r['chars_per_second'] for r in model_results) / len(model_results)
        
        print(f"{model}:")
        print(f"  Avg time: {avg_time:.1f}s")
        print(f"  Avg entities: {avg_entities:.1f}")
        print(f"  Avg speed: {avg_speed:.0f} chars/sec")

# Run performance analysis
analyze_processing_performance()
```

---

These examples showcase the full power of local AI processing with Ollama. The system provides privacy, performance, and flexibility for all your email parsing needs! 🚀