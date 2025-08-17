# CLI Usage Guide - Em-AI-lyze

This guide covers all command-line interfaces available in Em-AI-lyze, including the main CLI and RAG management CLI.

## Table of Contents

- [Overview](#overview)
- [Main CLI](#main-cli)
- [RAG CLI](#rag-cli)
- [MCP Server CLI](#mcp-server-cli)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

## Overview

Em-AI-lyze provides three main command-line interfaces:

1. **Main CLI** (`cli.py`) - Email parsing and analysis
2. **RAG CLI** (`rag_cli.py`) - Knowledge base management
3. **MCP Server CLI** (`main.py`) - Server operations

## Main CLI

### Prerequisites

```bash
# Activate virtual environment
source .venv/bin/activate

# Test system
python cli.py test
```

### Basic Commands

#### Parse Single Email

```bash
# Parse with local AI (default)
python cli.py parse --file /path/to/email.msg

# Parse with detailed output
python cli.py parse --file /path/to/email.msg --output detailed

# Parse with JSON output
python cli.py parse --file /path/to/email.msg --output json

# Use cloud AI (requires API key)
export GOOGLE_API_KEY="your-api-key"
python cli.py parse --file /path/to/email.msg --cloud
```

**Sample Output:**
```
✅ Email parsed successfully!

📧 Email Summary:
Subject: Budget Review Meeting - Action Required
From: manager@company.com
To: team@company.com
Date: 2024-01-15 14:30:00
AI Summary: Budget review meeting scheduled for Q4 analysis with department heads
Sentiment: neutral
Priority: high
Categories: meeting, budget, urgent, financial_review
Correlation Score: 0.842
Knowledge Confidence: 0.75
```

#### Parse Email Folder

```bash
# Parse all .msg files in folder
python cli.py parse-folder --folder /path/to/emails/

# Parse with detailed statistics
python cli.py parse-folder --folder /path/to/emails/ --output detailed

# Use cloud AI for folder processing
python cli.py parse-folder --folder /path/to/emails/ --cloud --model gemini-1.5-flash
```

**Sample Output:**
```
🔍 Found 25 email files
🤖 Using local AI model: mistral:latest
✅ Parsed: budget_review.msg
✅ Parsed: meeting_invite.msg
❌ Failed: corrupted_email.msg

📊 Results: 24/25 emails parsed successfully

📈 Summary Statistics:
Categories:
  meeting: 8 emails
  budget: 5 emails
  urgent: 3 emails
  
Sentiments:
  neutral: 18 emails
  positive: 4 emails
  negative: 2 emails
  
Priorities:
  high: 6 emails
  medium: 15 emails
  low: 3 emails
```

#### Extract Entities from Text

```bash
# Extract entities from arbitrary text
python cli.py extract --text "Meeting tomorrow at 2 PM with John Smith at Microsoft. Budget is $50,000."

# Use specific AI model
python cli.py extract --text "Contact Sarah at ext 1234" --model llama3.2:1b

# Use cloud AI
python cli.py extract --text "Invoice #12345 due by Friday" --cloud
```

**Sample Output:**
```
🔍 Extracting entities from text...
🤖 Using local AI model: mistral:latest
✓ Extraction processing complete

🔍 Extracted Entities:
📧 people: John Smith, Sarah
🏢 organizations: Microsoft
📅 dates: tomorrow at 2 PM, Friday
💰 money: $50,000
📞 phones: ext 1234
🏷️ events: Meeting
```

#### Compare Processing Methods

```bash
# Compare local vs cloud vs regex processing
python cli.py compare --file /path/to/email.msg
```

**Sample Output:**
```
🔄 Comparing Local vs Cloud Processing
File: email.msg
==================================================

🏠 LOCAL AI PROCESSING:
-------------------------
Model: mistral:latest
✅ Success
Summary: Budget review meeting scheduled...
Sentiment: neutral
Categories: meeting, budget, urgent
Entities: 12

☁️ CLOUD AI PROCESSING:
-------------------------
✅ Success
Summary: Quarterly budget analysis meeting...
Sentiment: neutral
Categories: meeting, financial_review, urgent
Entities: 15

🔧 REGEX-ONLY PROCESSING:
-------------------------
✅ Success
Categories: meeting, urgent
Entities: 8
```

#### Test System Setup

```bash
python cli.py test
```

### Command Reference

#### `parse` - Parse Single Email

**Syntax:** `python cli.py parse --file FILE [OPTIONS]`

**Required Arguments:**
- `--file FILE` - Path to .msg email file

**Options:**
- `--local` - Use local Ollama models (default: true)
- `--cloud` - Use cloud AI (requires API key)
- `--model MODEL` - AI model to use (default: auto)
- `--output FORMAT` - Output format: summary, detailed, json (default: summary)

#### `parse-folder` - Parse Email Folder

**Syntax:** `python cli.py parse-folder --folder FOLDER [OPTIONS]`

**Required Arguments:**
- `--folder FOLDER` - Path to folder containing .msg files

**Options:**
- `--local` - Use local Ollama models (default: true)
- `--cloud` - Use cloud AI (requires API key)
- `--model MODEL` - AI model to use (default: auto)
- `--output FORMAT` - Output format: summary, detailed (default: summary)

#### `extract` - Extract Entities

**Syntax:** `python cli.py extract --text TEXT [OPTIONS]`

**Required Arguments:**
- `--text TEXT` - Text to analyze

**Options:**
- `--local` - Use local Ollama models (default: true)
- `--cloud` - Use cloud AI (requires API key)
- `--model MODEL` - AI model to use (default: auto)

#### `compare` - Compare Processing Methods

**Syntax:** `python cli.py compare --file FILE`

**Required Arguments:**
- `--file FILE` - Path to .msg email file

#### `test` - Test System Setup

**Syntax:** `python cli.py test`

---

## RAG CLI

The RAG CLI manages the email knowledge base for enhanced contextual analysis.

### Prerequisites

```bash
# Install RAG dependencies
uv pip install ".[rag]"

# Test RAG system
python -m src.email_parser.rag_cli stats
```

### Command Reference

#### `import` - Import Emails to Knowledge Base

```bash
# Import all .msg files from folder
python -m src.email_parser.rag_cli import /path/to/emails/

# Import with custom pattern
python -m src.email_parser.rag_cli import /path/to/emails/ --pattern "*.msg"

# Use custom knowledge base
python -m src.email_parser.rag_cli --knowledge-base ./my_kb import /path/to/emails/
```

#### `search` - Search Knowledge Base

```bash
# Search for similar emails
python -m src.email_parser.rag_cli search "budget meeting"

# Get more results
python -m src.email_parser.rag_cli search "invoice payment" --max-results 10
```

#### `stats` - Knowledge Base Statistics

```bash
python -m src.email_parser.rag_cli stats
```

#### `export` - Export Knowledge Base

```bash
# Export to backup file
python -m src.email_parser.rag_cli export knowledge_backup.json

# Export with timestamp
python -m src.email_parser.rag_cli export "backup_$(date +%Y%m%d).json"
```

#### `test` - Test RAG Retrieval

```bash
python -m src.email_parser.rag_cli test "Budget Review" "We need to review Q4 spending"
```

#### `clear` - Clear Knowledge Base

```bash
python -m src.email_parser.rag_cli clear
# Requires confirmation: type 'yes'
```

For detailed RAG CLI documentation, see [RAG CLI Guide](RAG_CLI_Guide.md).

---

## MCP Server CLI

### Start MCP Server

```bash
# Start with local AI
python -m src.email_parser.main --mcp --local

# Start with cloud AI
export GOOGLE_API_KEY="your-api-key"
python -m src.email_parser.main --mcp

# Demo mode
python -m src.email_parser.main --demo
```

### HTTP/WebSocket Servers

```bash
# Start HTTP server
python -m src.email_parser.transports --transport http --port 8000

# Start WebSocket server
python -m src.email_parser.transports --transport websocket --port 8001
```

---

## Common Workflows

### Complete Setup and Processing

```bash
# 1. Setup and test
source .venv/bin/activate
uv pip install ".[all]"
python cli.py test

# 2. Build knowledge base
python -m src.email_parser.rag_cli import ./historical_emails/
python -m src.email_parser.rag_cli stats

# 3. Process new emails with RAG context
python cli.py parse --file new_email.msg

# 4. Start MCP server for Claude Desktop
python -m src.email_parser.main --mcp --local
```

### Batch Processing with RAG

```bash
# 1. Import historical emails
python -m src.email_parser.rag_cli import ./emails_archive/

# 2. Process new batch with enhanced context
python cli.py parse-folder --folder ./new_emails_batch/

# 3. Search for patterns
python -m src.email_parser.rag_cli search "contract approval"
python -m src.email_parser.rag_cli search "budget overrun"

# 4. Export analysis results
python -m src.email_parser.rag_cli export analysis_backup.json
```

### Development and Testing

```bash
# Test different AI models
python cli.py extract --text "Test message" --model llama3.2:1b
python cli.py extract --text "Test message" --model mistral:latest

# Compare processing methods
python cli.py compare --file test_email.msg

# Test RAG retrieval
python -m src.email_parser.rag_cli test "Meeting" "Budget review session"

# Monitor knowledge base growth
watch -n 60 python -m src.email_parser.rag_cli stats
```

---

## Environment Variables

### AI Configuration

```bash
# Cloud AI (Gemini)
export GOOGLE_API_KEY="your-gemini-api-key"

# Ollama configuration (optional)
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_NUM_PARALLEL=2
```

### RAG Configuration

```bash
# Knowledge base location
export EMAIL_KNOWLEDGE_BASE_PATH="./custom_kb"

# Embedding model
export RAG_EMBEDDING_MODEL="all-MiniLM-L6-v2"

# Vector database settings
export CHROMA_PERSIST_DIRECTORY="./vector_db"
```

---

## Troubleshooting

### Common Issues

#### CLI Not Working

```bash
# Check virtual environment
which python
source .venv/bin/activate

# Verify installation
python -c "from src.email_parser.parser import EmailParser; print('OK')"

# Run system test
python cli.py test
```

#### AI Model Issues

```bash
# Check Ollama models
ollama list

# Pull recommended model
ollama pull llama3.2:1b

# Test AI extraction
python cli.py extract --text "test message" --local
```

#### RAG Dependencies Missing

```bash
# Reinstall RAG dependencies
uv pip install ".[rag]"

# Test RAG system
python -c "import chromadb, sentence_transformers; print('RAG dependencies OK')"

# Check knowledge base
python -m src.email_parser.rag_cli stats
```

### Error Messages

#### "API key not provided"

```bash
# For cloud AI, set API key
export GOOGLE_API_KEY="your-api-key"

# Or use local AI instead
python cli.py parse --file email.msg --local
```

#### "No .msg files found"

```bash
# Check file extensions
ls -la /path/to/emails/*.msg

# Verify folder path
python cli.py parse-folder --folder /correct/path/
```

#### "ChromaDB not available"

```bash
# Install RAG dependencies
uv pip install chromadb sentence-transformers

# Or disable RAG
python cli.py parse --file email.msg  # Works without RAG
```

### Debug Mode

```bash
# Enable verbose logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
" && python cli.py parse --file email.msg

# Check log files
tail -f logs/email_parser.log  # If logging configured
```

### Performance Issues

```bash
# Use lightweight local model
python cli.py parse --file email.msg --model llama3.2:1b

# Process smaller batches
python cli.py parse-folder --folder /path/with/fewer/emails/

# Monitor system resources
htop  # Check CPU/memory usage during processing
```

---

## Advanced Usage

### Custom Knowledge Base Locations

```bash
# Use project-specific knowledge base
python -m src.email_parser.rag_cli --knowledge-base ./project_kb import ./project_emails/

# Use date-based knowledge base
KB_PATH="./kb_$(date +%Y_%m)"
python -m src.email_parser.rag_cli --knowledge-base $KB_PATH import ./monthly_emails/
```

### Scripting and Automation

```bash
#!/bin/bash
# Email processing automation script

# Variables
EMAILS_DIR="/path/to/new/emails"
KB_PATH="./production_kb"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Import new emails
echo "Importing new emails..."
python -m src.email_parser.rag_cli --knowledge-base $KB_PATH import $EMAILS_DIR

# Process with enhanced context
echo "Processing emails with RAG context..."
python cli.py parse-folder --folder $EMAILS_DIR --output detailed > "analysis_$DATE.json"

# Create backup
echo "Creating backup..."
python -m src.email_parser.rag_cli --knowledge-base $KB_PATH export "$BACKUP_DIR/backup_$DATE.json"

# Generate statistics report
echo "Generating report..."
python -m src.email_parser.rag_cli --knowledge-base $KB_PATH stats > "stats_$DATE.json"

echo "Processing complete!"
```

### Integration with Other Tools

```bash
# Pipe results to other tools
python cli.py parse --file email.msg --output json | jq '.categories'

# Process multiple files with xargs
find /emails -name "*.msg" -print0 | xargs -0 -I {} python cli.py parse --file {}

# Generate CSV report
python cli.py parse-folder --folder /emails/ --output json | \
  jq -r '[.subject, .sender, .sentiment, (.categories | join(";"))] | @csv'
```

The CLI provides comprehensive tools for email analysis, knowledge base management, and server operations. Start with the basic commands and gradually incorporate RAG and advanced features as needed.