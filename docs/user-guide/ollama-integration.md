# Ollama Integration Guide

Complete guide to using local AI models with Ollama for privacy-first email parsing.

## 🏠 Why Use Ollama?

- **🔒 Complete Privacy**: All processing happens locally on your machine
- **💰 No API Costs**: No cloud API fees or rate limits
- **⚡ Fast Processing**: Direct access to your local GPU/CPU
- **🛡️ Offline Capable**: Works without internet connection
- **🎯 Customizable**: Use any Ollama-supported model

## 📦 Installation & Setup

### 1. Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or visit https://ollama.ai for other platforms
```

### 2. Install Recommended Models
```bash
# Lightweight & Fast (1.3GB) - Great for basic extraction
ollama pull llama3.2:1b

# Balanced Performance (2.2GB) - Recommended for most users
ollama pull phi3:mini

# High Accuracy (4GB+) - Best results for complex emails
ollama pull llama3.1:latest
ollama pull mistral:latest
```

### 3. Install Email Parser with AI Support
```bash
uv pip install 'email-parsing-mcp[ai]'
```

## 🚀 Usage Examples

### Basic Local AI Parsing
```python
from email_parser.parser import EmailParser
from pathlib import Path

# Initialize with local AI (auto-detects best model)
parser = EmailParser(use_ai=True, use_local=True)

# Parse an email file
email_data = parser.parse_msg_file(Path("important.msg"))

print(f"AI Summary: {email_data.ai_summary}")
print(f"Sentiment: {email_data.sentiment}")
print(f"Priority: {email_data.ai_priority}")
print(f"Categories: {email_data.categories}")
```

### Specify a Particular Model
```python
# Use a specific local model
parser = EmailParser(
    use_ai=True, 
    use_local=True, 
    ai_model="llama3.2:1b"
)
```

### Entity Extraction from Text
```python
parser = EmailParser(use_ai=True, use_local=True)

text = """
Hi John, 
Can you join the budget meeting tomorrow at 3 PM? 
We need to discuss the $150,000 allocation.
Contact me at mike@company.com or 555-123-4567.
"""

entities = parser.extract_entities_from_text(text)
print(entities)
# Output:
# {
#   'people': ['John', 'Mike'],
#   'emails': ['mike@company.com'],
#   'phones': ['555-123-4567'],
#   'money': ['$150,000'],
#   'dates': ['tomorrow at 3 PM'],
#   'events': ['budget meeting']
# }
```

## 🖥️ Command Line Usage

### Start MCP Server with Ollama
```bash
# Auto-detect best local model
python -m src.email_parser.main --mcp --local

# Use specific model
python -m src.email_parser.main --mcp --local --model "phi3:mini"
```

### CLI Commands with Ollama
```bash
# Parse single email with local AI
python cli.py parse --file email.msg --local

# Parse entire folder
python cli.py parse-folder --folder emails/ --local --output detailed

# Extract entities from text
python cli.py extract --text "Meeting with Sarah tomorrow" --local

# Compare local vs cloud processing
python cli.py compare --file email.msg
```

## 🔗 Claude Desktop Integration

Add this configuration to your Claude Desktop settings:

```json
{
  "mcpServers": {
    "email-parser-local": {
      "command": "python",
      "args": ["-m", "src.email_parser.main", "--mcp", "--local"],
      "cwd": "/path/to/email-parser"
    }
  }
}
```

**Benefits in Claude Desktop:**
- No API key required
- Instant processing
- Complete privacy
- Works offline

## 🎯 Model Recommendations

### For Different Use Cases

| Use Case | Recommended Model | Size | Speed | Accuracy |
|----------|-------------------|------|-------|----------|
| **High Volume Processing** | `llama3.2:1b` | 1.3GB | ⚡⚡⚡ | ⭐⭐⭐ |
| **Balanced Performance** | `phi3:mini` | 2.2GB | ⚡⚡ | ⭐⭐⭐⭐ |
| **Complex Analysis** | `llama3.1:latest` | 4GB+ | ⚡ | ⭐⭐⭐⭐⭐ |
| **Best Accuracy** | `mistral:latest` | 7GB+ | ⚡ | ⭐⭐⭐⭐⭐ |

### Performance Comparison
```bash
# Test different models on your hardware
python test_ollama.py

# Compare processing speeds
python benchmark_models.py
```

## 🛠️ Advanced Configuration

### Custom Model Settings
```python
from email_parser.ai_extractor import AIEmailExtractor

# Custom extractor with specific model
extractor = AIEmailExtractor(
    model_id="mistral:latest",
    use_local=True
)

# Use in parser
parser = EmailParser(use_ai=True)
parser.ai_extractor = extractor
```

### MCP Server with Custom Settings
```python
from email_parser.mcp_server import EmailParserMCPServer

server = EmailParserMCPServer(
    name="custom-email-parser",
    use_ai=True,
    use_local=True,
    ai_model="phi3:mini"
)
```

## 🔧 Troubleshooting

### Common Issues

**Model Not Found:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.2:1b
```

**Slow Processing:**
```bash
# Check Ollama status
ollama ps

# Restart Ollama service
sudo systemctl restart ollama  # Linux
brew services restart ollama    # macOS
```

**Memory Issues:**
- Use smaller models like `llama3.2:1b` for limited RAM
- Close other applications during processing
- Consider using CPU-only models for lower memory usage

### Performance Optimization

**GPU Acceleration:**
```bash
# Check GPU support
ollama run llama3.2:1b --verbose

# Force GPU usage (if available)
OLLAMA_GPU_LAYERS=32 ollama run phi3:mini
```

**Model Caching:**
```python
# Preload model to avoid cold starts
parser = EmailParser(use_ai=True, use_local=True)
# First call loads model into memory
parser.extract_entities_from_text("warmup text")
```

## 📊 Monitoring & Logging

### Enable Debug Logging
```python
import logging
logging.getLogger('langextract').setLevel(logging.DEBUG)

# See detailed processing information
parser = EmailParser(use_ai=True, use_local=True)
```

### Performance Metrics
```bash
# Run with timing information
python -m src.email_parser.main --mcp --local --verbose

# Monitor resource usage
htop  # or Activity Monitor on macOS
```

## 🎉 Next Steps

1. **Try Different Models**: Experiment with various Ollama models
2. **Benchmark Performance**: Test on your specific email types
3. **Integrate with Applications**: Use the MCP server in your workflows
4. **Contribute**: Help improve local AI support

---

**Need help?** Check the [troubleshooting section](#troubleshooting) or open an issue on GitHub!