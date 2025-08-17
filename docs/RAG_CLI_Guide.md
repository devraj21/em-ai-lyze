# RAG CLI Guide - Email Knowledge Base Management

The RAG CLI provides comprehensive management tools for the email knowledge base, enabling you to build, search, and maintain a semantic database of processed emails for enhanced analysis.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Workflow Examples](#workflow-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Install RAG dependencies
uv pip install ".[rag]"

# Or install everything
uv pip install ".[all]"
```

### Dependencies Installed

- **ChromaDB**: Vector database for semantic storage
- **Sentence Transformers**: Embedding model for semantic similarity
- **NumPy**: Numerical operations for embeddings

## Quick Start

### 1. Test RAG System

```bash
python -m src.email_parser.rag_cli stats
```

**Expected Output:**
```json
{
  "total_emails": 0,
  "total_categories": 0,
  "top_categories": {},
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_db_available": true
}
```

### 2. Import Historical Emails

```bash
python -m src.email_parser.rag_cli import /path/to/emails/
```

### 3. Search Knowledge Base

```bash
python -m src.email_parser.rag_cli search "budget meeting"
```

## Command Reference

### Basic Syntax

```bash
python -m src.email_parser.rag_cli [--knowledge-base PATH] COMMAND [OPTIONS]
```

### Global Options

| Option | Default | Description |
|--------|---------|-------------|
| `--knowledge-base PATH` | `./email_knowledge_base` | Path to knowledge base directory |

---

## Commands

### `import` - Import Emails to Knowledge Base

Import `.msg` files from a folder into the knowledge base for future retrieval.

**Syntax:**
```bash
python -m src.email_parser.rag_cli import FOLDER [OPTIONS]
```

**Arguments:**
- `FOLDER` - Directory containing `.msg` files

**Options:**
- `--pattern PATTERN` - File pattern to match (default: `*.msg`)

**Examples:**

```bash
# Import all .msg files from emails folder
python -m src.email_parser.rag_cli import ./sample_emails/

# Import with custom pattern
python -m src.email_parser.rag_cli import ./emails/ --pattern "*.msg"

# Use custom knowledge base location
python -m src.email_parser.rag_cli --knowledge-base ./my_kb import ./emails/
```

**Sample Output:**
```
🔄 Importing 25 email files from ./sample_emails/
   Processing: budget_review.msg
   Processing: invoice_approval.msg
   Processing: meeting_invite.msg
   ...
✅ Import completed: 23 processed, 2 failed
{
  "total_files": 25,
  "processed": 23,
  "failed": 2,
  "errors": [
    "Failed to parse: corrupted_email.msg",
    "Failed to store: duplicate_email.msg"
  ]
}
```

---

### `search` - Search Knowledge Base

Search for emails similar to a query using semantic similarity.

**Syntax:**
```bash
python -m src.email_parser.rag_cli search QUERY [OPTIONS]
```

**Arguments:**
- `QUERY` - Search query text

**Options:**
- `--max-results N` - Maximum number of results (default: 5)

**Examples:**

```bash
# Basic search
python -m src.email_parser.rag_cli search "budget meeting"

# Get more results
python -m src.email_parser.rag_cli search "invoice payment" --max-results 10

# Search with complex query
python -m src.email_parser.rag_cli search "quarterly financial review presentation"
```

**Sample Output:**
```json
{
  "query": "budget meeting",
  "similar_emails": [
    {
      "id": "abc123def456",
      "subject": "Q4 Budget Review Meeting - Action Required",
      "summary": "Budget review meeting scheduled for quarterly analysis with department heads",
      "categories": ["meeting", "budget", "financial", "urgent"],
      "timestamp": "2024-01-10T14:30:00"
    },
    {
      "id": "def456ghi789", 
      "subject": "Monthly Budget Discussion",
      "summary": "Regular monthly budget review and planning session",
      "categories": ["meeting", "budget", "monthly"],
      "timestamp": "2024-01-05T10:15:00"
    }
  ],
  "context_summary": "Found 5 similar budget-related emails. Common categories: meeting, budget, financial. Typical sentiment: neutral.",
  "confidence": 0.85
}
```

---

### `stats` - Knowledge Base Statistics

Display statistics about the current knowledge base.

**Syntax:**
```bash
python -m src.email_parser.rag_cli stats
```

**Sample Output:**
```json
{
  "total_emails": 247,
  "total_categories": 15,
  "top_categories": {
    "meeting": 85,
    "budget": 45,
    "invoice": 38,
    "urgent": 32,
    "report": 28,
    "contract": 19
  },
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_db_available": true
}
```

---

### `export` - Export Knowledge Base

Export the knowledge base to a JSON file for backup or analysis.

**Syntax:**
```bash
python -m src.email_parser.rag_cli export OUTPUT_FILE
```

**Arguments:**
- `OUTPUT_FILE` - Path to output JSON file

**Examples:**

```bash
# Export to backup file
python -m src.email_parser.rag_cli export knowledge_backup.json

# Export with timestamp
python -m src.email_parser.rag_cli export "backup_$(date +%Y%m%d).json"
```

**Sample Output:**
```json
{
  "success": true,
  "exported_emails": 247,
  "output_file": "knowledge_backup.json"
}
```

**Export File Structure:**
```json
{
  "export_date": "/path/to/current/directory",
  "total_emails": 247,
  "emails": [
    {
      "id": "email_hash_id",
      "subject": "Budget Review Meeting",
      "body_summary": "Quarterly budget analysis and planning session",
      "categories": ["meeting", "budget"],
      "entities": {
        "emails": ["john@company.com"],
        "dates": ["2024-01-15"],
        "money": ["$50000"]
      },
      "patterns": {
        "correlation_score": 0.85,
        "priority": "high",
        "sentiment": "neutral"
      },
      "context": {
        "sender": "manager@company.com",
        "recipients_count": 5,
        "body_length": 425
      },
      "timestamp": "2024-01-15T14:30:00"
    }
  ]
}
```

---

### `test` - Test RAG Retrieval

Test the RAG system with sample content to verify functionality.

**Syntax:**
```bash
python -m src.email_parser.rag_cli test SUBJECT BODY
```

**Arguments:**
- `SUBJECT` - Test email subject
- `BODY` - Test email body content

**Examples:**

```bash
# Test basic retrieval
python -m src.email_parser.rag_cli test "Budget Review" "We need to review Q4 spending"

# Test complex content
python -m src.email_parser.rag_cli test \
  "Quarterly Financial Analysis" \
  "Please prepare financial reports for the Q4 board meeting. Include variance analysis and budget projections for next quarter."
```

**Sample Output:**
```json
{
  "test_subject": "Budget Review",
  "test_body": "We need to review Q4 spending and discuss budget allocations...",
  "similar_emails_found": 3,
  "context_summary": "Found 3 similar budget-related emails. Common categories: budget, meeting, financial. Typical sentiment: neutral.",
  "suggested_categories": ["budget", "financial_review", "quarterly"],
  "confidence_score": 0.78,
  "relevant_patterns": {
    "avg_correlation_score": 0.82,
    "common_priorities": {"high": 2, "medium": 1},
    "attachment_patterns": {"spreadsheet": 2, "document": 1},
    "sender_patterns": {"finance@company.com": 2, "manager@company.com": 1}
  }
}
```

---

### `clear` - Clear Knowledge Base

**⚠️ DANGEROUS**: Delete all data from the knowledge base.

**Syntax:**
```bash
python -m src.email_parser.rag_cli clear
```

**Interactive Confirmation:**
```
⚠️  This will delete ALL knowledge base data. Type 'yes' to confirm: yes
{
  "success": true
}
```

**Safety Notes:**
- Always export your knowledge base before clearing
- This action cannot be undone
- Confirmation required to prevent accidental deletion

---

## Workflow Examples

### Complete Setup Workflow

```bash
# 1. Install dependencies
uv pip install ".[rag]"

# 2. Test system
python -m src.email_parser.rag_cli stats

# 3. Import historical emails
python -m src.email_parser.rag_cli import ./historical_emails/

# 4. Verify import
python -m src.email_parser.rag_cli stats

# 5. Test retrieval
python -m src.email_parser.rag_cli search "meeting"

# 6. Create backup
python -m src.email_parser.rag_cli export backup_$(date +%Y%m%d).json
```

### Incremental Email Processing

```bash
# Import new emails periodically
python -m src.email_parser.rag_cli import ./new_emails_jan/
python -m src.email_parser.rag_cli import ./new_emails_feb/

# Monitor knowledge base growth
python -m src.email_parser.rag_cli stats

# Search for patterns
python -m src.email_parser.rag_cli search "quarterly review"
python -m src.email_parser.rag_cli search "budget approval"
```

### Multi-Environment Setup

```bash
# Development knowledge base
python -m src.email_parser.rag_cli --knowledge-base ./dev_kb import ./test_emails/

# Production knowledge base  
python -m src.email_parser.rag_cli --knowledge-base ./prod_kb import ./production_emails/

# Search across different environments
python -m src.email_parser.rag_cli --knowledge-base ./dev_kb search "test data"
python -m src.email_parser.rag_cli --knowledge-base ./prod_kb search "production issue"
```

## Best Practices

### 1. Knowledge Base Organization

```bash
# Use descriptive knowledge base names
--knowledge-base ./email_kb_2024
--knowledge-base ./customer_emails_kb
--knowledge-base ./internal_communications_kb
```

### 2. Regular Maintenance

```bash
# Weekly backup routine
#!/bin/bash
DATE=$(date +%Y%m%d)
python -m src.email_parser.rag_cli export "weekly_backup_${DATE}.json"
echo "Backup created: weekly_backup_${DATE}.json"

# Monthly statistics report
python -m src.email_parser.rag_cli stats > "monthly_stats_${DATE}.json"
```

### 3. Import Strategy

```bash
# Import in batches for large datasets
python -m src.email_parser.rag_cli import ./emails_2024_q1/
python -m src.email_parser.rag_cli import ./emails_2024_q2/
python -m src.email_parser.rag_cli import ./emails_2024_q3/
python -m src.email_parser.rag_cli import ./emails_2024_q4/
```

### 4. Search Optimization

```bash
# Use specific terms for better results
python -m src.email_parser.rag_cli search "budget approval process"  # Better
python -m src.email_parser.rag_cli search "budget"                   # Too broad

# Combine multiple searches for comprehensive analysis
python -m src.email_parser.rag_cli search "quarterly financial review"
python -m src.email_parser.rag_cli search "Q1 Q2 Q3 Q4 budget analysis"
python -m src.email_parser.rag_cli search "financial reporting deadline"
```

## Knowledge Base Structure

### Directory Layout
```
email_knowledge_base/
├── chroma_db/              # Vector database files
│   ├── chroma.sqlite3     # ChromaDB metadata
│   └── ...                # Embedding vectors
├── metadata.db           # SQLite metadata database
└── logs/                 # Operation logs (optional)
```

### Metadata Database Schema
```sql
CREATE TABLE email_knowledge (
    id TEXT PRIMARY KEY,           -- Unique email hash
    subject TEXT NOT NULL,         -- Email subject
    body_summary TEXT,            -- AI-generated summary
    categories TEXT,              -- JSON array of categories
    entities TEXT,                -- JSON object of extracted entities
    patterns TEXT,                -- JSON object of analysis patterns
    context TEXT,                 -- JSON object of metadata
    timestamp TEXT,               -- Email timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Integration with Email Parser

The RAG CLI works seamlessly with the main email parser:

```python
# Python integration
from src.email_parser.parser import EmailParser

# Initialize parser with RAG enabled
parser = EmailParser(
    use_ai=True,
    use_rag=True,
    knowledge_base_path="./email_knowledge_base"
)

# Parse email - automatically uses RAG for enhanced analysis
result = parser.parse_msg_file(Path("email.msg"))

# Access RAG-enhanced fields
print(f"Context confidence: {result.knowledge_confidence}")
print(f"Suggested categories: {result.suggested_categories}")
print(f"Context summary: {result.context_summary}")
```

## Troubleshooting

### Common Issues

#### 1. Import Failures
```bash
# Check file permissions
ls -la /path/to/emails/

# Verify .msg file format
file /path/to/emails/*.msg

# Test single file first
python -m src.email_parser.rag_cli import /path/to/single_email/
```

#### 2. Search Returns No Results
```bash
# Check knowledge base has data
python -m src.email_parser.rag_cli stats

# Try broader search terms
python -m src.email_parser.rag_cli search "meeting" --max-results 10

# Test with sample content
python -m src.email_parser.rag_cli test "Test Subject" "Test body content"
```

#### 3. Dependencies Missing
```bash
# Reinstall RAG dependencies
uv pip uninstall chromadb sentence-transformers
uv pip install ".[rag]"

# Check installation
python -c "import chromadb, sentence_transformers; print('Dependencies OK')"
```

#### 4. Knowledge Base Corruption
```bash
# Backup first if possible
python -m src.email_parser.rag_cli export emergency_backup.json

# Clear and rebuild
python -m src.email_parser.rag_cli clear
python -m src.email_parser.rag_cli import /path/to/emails/
```

### Performance Optimization

#### Large Knowledge Bases
```bash
# Import in smaller batches
find /large/email/archive -name "*.msg" | head -100 | xargs -I {} cp {} ./batch1/
python -m src.email_parser.rag_cli import ./batch1/
```

#### Search Performance
```bash
# Use specific queries for faster results
python -m src.email_parser.rag_cli search "budget Q4 2024" --max-results 5
```

### Debug Mode

```bash
# Enable verbose logging
export PYTHONPATH=.
python -m src.email_parser.rag_cli --knowledge-base ./debug_kb import ./test/ 2>&1 | tee import.log
```

## Support

For issues and questions:
1. Check this documentation
2. Review the troubleshooting section
3. Examine log files in the knowledge base directory
4. Test with minimal examples

The RAG CLI provides powerful tools for building and maintaining an intelligent email knowledge base that continuously improves the accuracy of email analysis through contextual learning.