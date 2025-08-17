# Getting Started

Welcome to Email Parser! This guide will help you set up and start using AI-powered email parsing with both cloud and local models.

## 🎯 What is Email Parser?

Email Parser is a powerful tool that extracts structured information from .msg email files using AI. It provides:

- **🤖 Dual AI Support**: Cloud (Gemini) and Local (Ollama) processing
- **🔒 Privacy-First**: Complete local processing option
- **📊 Rich Analysis**: Entities, sentiment, priorities, action items
- **🔧 MCP Integration**: Model Context Protocol for Claude Desktop
- **⚡ Fast Fallback**: Regex patterns when AI unavailable

## ⚡ Quick Start (5 minutes)

### Option 1: Local AI with Ollama (Recommended)
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Get a lightweight model
ollama pull llama3.2:1b

# 3. Install email parser
uv pip install 'email-parsing-mcp[ai]'

# 4. Test it works
python cli.py test

# 5. Parse an email
python cli.py parse --file your_email.msg --local
```

### Option 2: Cloud AI with Gemini
```bash
# 1. Install email parser
uv pip install 'email-parsing-mcp[ai]'

# 2. Set API key
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Parse an email
python cli.py parse --file your_email.msg
```

## 📦 Installation Options

### Core Installation
```bash
# Basic functionality (regex-based parsing)
uv pip install email-parsing-mcp
```

### AI-Enhanced Installation
```bash
# Full AI capabilities with LangExtract
uv pip install 'email-parsing-mcp[ai]'
```

### Network Integration
```bash
# Add HTTP/WebSocket server capabilities  
uv pip install 'email-parsing-mcp[network]'
```

### Complete Installation
```bash
# Everything included
uv pip install 'email-parsing-mcp[ai,network]'
```

## 🏠 Local AI Setup (Ollama)

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows/Manual:**
Visit [ollama.ai](https://ollama.ai) and download the installer.

### 2. Choose Your Model

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `llama3.2:1b` | 1.3GB | ⚡⚡⚡ | High-volume processing |
| `phi3:mini` | 2.2GB | ⚡⚡ | Balanced performance |
| `mistral:latest` | 7GB | ⚡ | Best accuracy |

```bash
# Install your chosen model
ollama pull llama3.2:1b    # Fast & lightweight
ollama pull phi3:mini      # Recommended balance
ollama pull mistral:latest # Best accuracy
```

### 3. Verify Setup
```bash
# Check available models
ollama list

# Test email parser
python cli.py test
```

## ☁️ Cloud AI Setup (Gemini)

### 1. Get API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 2. Set Environment Variable
```bash
# Linux/macOS
export GOOGLE_API_KEY="your-api-key-here"

# Windows
set GOOGLE_API_KEY=your-api-key-here

# Or add to your .bashrc/.zshrc for persistence
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### 3. Test Connection
```bash
python cli.py extract --text "Test message with john@example.com"
```

## 🎮 First Steps

### 1. Test Your Installation
```bash
python cli.py test
```

Expected output:
```
🧪 Testing Email Parser Setup
========================================
✅ Core parser import successful
✅ AI extractor import successful  
✅ Ollama is available
   Available models: 2
   • llama3.2:1b
   • phi3:mini
✅ Local AI parser initialization successful
   Using model: llama3.2:1b
✅ Basic parser initialization successful

🎉 Setup test completed!
```

### 2. Parse Your First Email
```bash
# With local AI (privacy-first)
python cli.py parse --file sample_email.msg --local

# With cloud AI (high accuracy)  
python cli.py parse --file sample_email.msg
```

### 3. Extract Entities from Text
```bash
python cli.py extract --text "Meeting with Sarah tomorrow at 2 PM about $50,000 budget" --local
```

Expected output:
```
🔍 Extracting entities from text...
🤖 Using local AI model: llama3.2:1b

📝 Input Text:
"Meeting with Sarah tomorrow at 2 PM about $50,000 budget"

🔍 Extracted Entities:
  • People: ['Sarah']
  • Money: ['$50,000']  
  • Dates: ['tomorrow at 2 PM']
  • Events: ['Meeting']

🤖 Processing: AI Enhanced
```

## 🔧 Usage Patterns

### CLI Usage
Perfect for command-line workflows and automation:
```bash
# Single file analysis
python cli.py parse --file email.msg --local --output detailed

# Batch folder processing
python cli.py parse-folder --folder emails/ --local

# Entity extraction
python cli.py extract --text "Your text here" --local
```

### Python API Usage
For programmatic integration:
```python
from email_parser.parser import EmailParser
from pathlib import Path

# Initialize with local AI
parser = EmailParser(use_ai=True, use_local=True)

# Parse an email
email_data = parser.parse_msg_file(Path("email.msg"))

# Access results
print(f"AI Summary: {email_data.ai_summary}")
print(f"Sentiment: {email_data.sentiment}")
print(f"Entities: {email_data.extracted_entities}")
```

### MCP Server Usage
For Claude Desktop integration:
```bash
# Start MCP server with local AI
python -m src.email_parser.main --mcp --local

# Or with cloud AI
python -m src.email_parser.main --mcp
```

## 🎛️ Configuration

### Model Selection
```python
# Specific local model
parser = EmailParser(
    use_ai=True, 
    use_local=True, 
    ai_model="phi3:mini"
)

# Cloud model
parser = EmailParser(
    use_ai=True, 
    use_local=False, 
    ai_model="gemini-1.5-flash"
)

# No AI (regex only)
parser = EmailParser(use_ai=False)
```

### Environment Variables
```bash
# For cloud AI
export GOOGLE_API_KEY="your-key"

# For custom Ollama endpoint
export OLLAMA_HOST="http://localhost:11434"

# For logging level
export LOG_LEVEL="DEBUG"
```

## 🏗️ Project Structure

After installation, you can use the library in several ways:

```
email-parser/
├── cli.py                    # Command-line interface
├── src/email_parser/         # Core library
│   ├── parser.py            # Main EmailParser class
│   ├── ai_extractor.py      # AI-powered extraction
│   ├── mcp_server.py        # MCP server implementation
│   └── main.py              # Entry points
├── docs/                    # Documentation
└── examples/                # Usage examples
```

## 🎯 Next Steps

### For CLI Users
1. **[CLI Usage Guide](cli-usage.md)** - Learn all CLI commands and options
2. **[Ollama Integration](ollama-integration.md)** - Deep dive into local AI setup

### For Developers
1. **[Parser API](../api/parser-api.md)** - Python API documentation
2. **[Examples](../examples/basic-usage.md)** - Code examples and patterns

### For Claude Desktop Users
1. **[MCP Server Guide](mcp-server.md)** - Set up the MCP server
2. **[Claude Desktop Examples](../examples/claude-desktop.md)** - Integration examples

## ❓ Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the right environment
source .venv/bin/activate  # If using virtual environment

# Install missing dependencies
uv pip install 'email-parsing-mcp[ai]'
```

**Ollama not found:**
```bash
# Check Ollama is running
ollama list

# Restart Ollama if needed (macOS)
brew services restart ollama
```

**No models available:**
```bash
# Pull a recommended model
ollama pull llama3.2:1b
```

**API key issues:**
```bash
# Verify key is set
echo $GOOGLE_API_KEY

# Test with simple request
python cli.py extract --text "test" # Should use cloud AI
```

### Getting Help

- **Documentation**: Check the [docs/](.) folder
- **Examples**: See [examples/](../examples/) for code samples
- **Issues**: Report bugs on GitHub
- **CLI Help**: Run `python cli.py --help` for command info

---

🎉 **You're ready to start parsing emails with AI!** Choose your preferred method and dive into the specific guides above.