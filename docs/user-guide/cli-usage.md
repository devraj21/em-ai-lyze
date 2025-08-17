# CLI Usage Guide

Comprehensive guide to using the Email Parser command-line interface with AI and Ollama support.

## 🚀 Quick Start

```bash
# Test your setup
python cli.py test

# Parse a single email with local AI
python cli.py parse --file email.msg --local

# Extract entities from text
python cli.py extract --text "Meeting tomorrow at 2 PM" --local
```

## 📋 Available Commands

### `test` - Test Installation
Verify that all components are working properly.

```bash
python cli.py test
```

**What it checks:**
- ✅ Core parser imports
- ✅ AI extractor availability  
- ✅ Ollama installation and models
- ✅ Parser initialization with different modes

### `parse` - Parse Single Email File
Parse a single .msg email file with detailed analysis.

```bash
# Basic usage with local AI
python cli.py parse --file email.msg --local

# Use specific model
python cli.py parse --file email.msg --local --model "llama3.2:1b"

# Different output formats
python cli.py parse --file email.msg --local --output detailed
python cli.py parse --file email.msg --local --output json
```

**Options:**
- `--file`: Path to .msg email file (required)
- `--local`: Use local Ollama models instead of cloud AI
- `--model`: Specify AI model (default: gemini-1.5-flash)
- `--output`: Output format (summary, detailed, json)

### `parse-folder` - Parse Multiple Emails
Process all .msg files in a folder with batch analysis.

```bash
# Parse folder with local AI
python cli.py parse-folder --folder emails/ --local

# Detailed analysis of all emails
python cli.py parse-folder --folder emails/ --local --output detailed

# Use specific model for batch processing
python cli.py parse-folder --folder emails/ --local --model "phi3:mini"
```

**Options:**
- `--folder`: Path to folder containing .msg files (required)
- `--local`: Use local Ollama models
- `--model`: Specify AI model
- `--output`: Output format (summary, detailed)

**Output includes:**
- Individual file processing status
- Success/failure statistics
- Category distribution analysis
- Sentiment analysis summary
- Priority distribution

### `extract` - Entity Extraction
Extract entities from arbitrary text using AI or regex patterns.

```bash
# Extract with local AI
python cli.py extract --text "Meeting with John at john@company.com tomorrow at 3 PM about $50k budget" --local

# Extract with cloud AI
python cli.py extract --text "Call Sarah at 555-123-4567 about the December meeting"

# Use specific model
python cli.py extract --text "Budget meeting in Conference Room A" --local --model "mistral:latest"
```

**Options:**
- `--text`: Text to analyze (required)
- `--local`: Use local Ollama models
- `--model`: Specify AI model

**Extracts:**
- 👥 People names
- 📧 Email addresses  
- 📞 Phone numbers
- 💰 Monetary amounts
- 📅 Dates and times
- 🏢 Organizations
- 📍 Locations
- 🎯 Events and meetings

### `compare` - Compare Processing Methods
Compare local AI, cloud AI, and regex-only processing on the same file.

```bash
python cli.py compare --file email.msg
```

**Shows comparison of:**
- 🏠 Local AI (Ollama) results
- ☁️ Cloud AI (Gemini) results  
- 🔧 Regex-only results

**Useful for:**
- Evaluating model performance
- Choosing the right processing method
- Debugging extraction issues

## 🎯 Usage Examples

### Basic Email Analysis
```bash
# Quick analysis with local AI
python cli.py parse --file important_email.msg --local

# Output:
# 🔍 Parsing email file: important_email.msg  
# 🤖 Using local AI model: llama3.2:1b
# ✅ Email parsed successfully!
#
# 📧 Email Summary:
# Subject: Q4 Budget Meeting Tomorrow
# From: manager@company.com
# To: team@company.com
# AI Summary: Team meeting scheduled for Q4 budget review...
# Sentiment: neutral
# Priority: high
# Categories: meeting, budget, urgent
```

### Detailed Folder Analysis
```bash
# Analyze entire email folder
python cli.py parse-folder --folder ./sample_emails --local --output detailed

# Output:
# 🔍 Found 15 email files
# 🤖 Using local AI model: mistral:latest
# ✅ Parsed: budget_email.msg
# ✅ Parsed: meeting_invite.msg
# ...
# 📊 Results: 14/15 emails parsed successfully
#
# 📈 Analysis Summary:
# Top Categories: {'meeting': 8, 'budget': 5, 'urgent': 3}
# Sentiment Distribution: {'neutral': 9, 'positive': 4, 'negative': 1}
# Priority Distribution: {'medium': 7, 'high': 5, 'low': 2}
```

### Entity Extraction Examples
```bash
# Extract entities from meeting text
python cli.py extract --text "Budget meeting with Sarah Johnson tomorrow at 2 PM EST in Conference Room B. Budget is $150,000 for Q4. Contact sarah@company.com or 555-123-4567." --local

# Output:
# 🔍 Extracting entities from text...
# 🤖 Using local AI model: phi3:mini
#
# 📝 Input Text:
# "Budget meeting with Sarah Johnson tomorrow at 2 PM EST..."
#
# 🔍 Extracted Entities:
#   • People: ['Sarah Johnson']
#   • Emails: ['sarah@company.com'] 
#   • Phones: ['555-123-4567']
#   • Money: ['$150,000']
#   • Dates: ['tomorrow at 2 PM EST']
#   • Events: ['Budget meeting']
#   • Locations: ['Conference Room B']
#
# 🤖 Processing: AI Enhanced
```

### Performance Comparison
```bash
# Compare different processing methods
python cli.py compare --file complex_email.msg

# Output:
# 🔄 Comparing Local vs Cloud Processing
# File: complex_email.msg
# ===================================
#
# 🏠 LOCAL AI PROCESSING:
# -------------------------
# Model: mistral:latest
# ✅ Success
# Summary: Detailed analysis of Q4 budget requirements...
# Sentiment: positive
# Categories: budget, planning, meeting
# Entities: 12
#
# ☁️ CLOUD AI PROCESSING:  
# -------------------------
# ✅ Success
# Summary: Q4 budget planning meeting with comprehensive analysis...
# Sentiment: positive
# Categories: budget, financial, meeting, planning
# Entities: 15
#
# 🔧 REGEX-ONLY PROCESSING:
# -------------------------  
# ✅ Success
# Categories: meeting, budget
# Entities: 8
```

## ⚙️ Configuration Options

### Model Selection
```bash
# Use fastest local model (good for high volume)
python cli.py parse --file email.msg --local --model "llama3.2:1b"

# Use balanced model (recommended)
python cli.py parse --file email.msg --local --model "phi3:mini"  

# Use high-accuracy model (best results)
python cli.py parse --file email.msg --local --model "mistral:latest"
```

### Output Formats

**Summary Format (default):**
- Basic email metadata
- AI-generated summary
- Sentiment and priority
- Key categories

**Detailed Format:**
- Complete email analysis
- Full entity extraction
- Action items identified
- Attachment information
- Correlation scores

**JSON Format:**
- Machine-readable output
- All extracted data
- Perfect for automation
- API integration ready

## 🛠️ Troubleshooting

### Common Issues

**"Missing dependencies" error:**
```bash
# Install AI dependencies
uv pip install 'email-parsing-mcp[ai]'
```

**"Ollama not found" error:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2:1b
```

**Slow processing:**
```bash
# Use faster model
python cli.py parse --file email.msg --local --model "llama3.2:1b"

# Or use regex-only mode
python cli.py parse --file email.msg  # (no --local, no cloud AI key)
```

### Performance Tips

1. **Model Selection:**
   - `llama3.2:1b` - Fastest, 1.3GB
   - `phi3:mini` - Balanced, 2.2GB  
   - `mistral:latest` - Best accuracy, 7GB+

2. **Batch Processing:**
   - Use `parse-folder` for multiple files
   - Local AI avoids API rate limits
   - Process folders overnight for large datasets

3. **Memory Management:**
   - Close other applications during processing
   - Use smaller models if memory is limited
   - Consider processing files in smaller batches

## 🔗 Integration Examples

### Shell Scripts
```bash
#!/bin/bash
# Process all emails in inbox
python cli.py parse-folder --folder ~/inbox --local --output json > analysis.json

# Send results to another system
curl -X POST -H "Content-Type: application/json" -d @analysis.json \
  http://api.example.com/email-analysis
```

### Python Automation
```python
import subprocess
import json

# Process email and get JSON result
result = subprocess.run([
    'python', 'cli.py', 'parse', 
    '--file', 'email.msg', 
    '--local', '--output', 'json'
], capture_output=True, text=True)

# Parse results
email_data = json.loads(result.stdout)
print(f"Sentiment: {email_data['sentiment']}")
```

## 📊 Performance Benchmarks

Typical processing times on modern hardware:

| Model | Single Email | 100 Emails | Memory Usage |
|-------|-------------|------------|--------------|
| `llama3.2:1b` | ~2s | ~3min | ~2GB |
| `phi3:mini` | ~5s | ~8min | ~3GB |  
| `mistral:latest` | ~15s | ~25min | ~8GB |
| Regex Only | <1s | ~30s | ~100MB |

---

**Next Steps:**
- Try different models on your specific email types
- Integrate CLI into your workflows
- Check out the [API documentation](../api/parser-api.md) for programmatic usage