# Em-AI-lyze Documentation

Welcome to Em-AI-lyze documentation! This project provides AI-powered email analysis capabilities with both cloud and local LLM support.

## 📚 Documentation Structure

### User Guides
- **[Getting Started](user-guide/getting-started.md)** - Quick setup and first steps
- **[Ollama Integration](user-guide/ollama-integration.md)** - Complete guide to local AI with Ollama
- **[CLI Usage](user-guide/cli-usage.md)** - Command-line interface guide
- **[MCP Server](user-guide/mcp-server.md)** - Model Context Protocol server setup

### API Reference
- **[Parser API](api/parser-api.md)** - EmailParser class documentation
- **[MCP Tools](api/mcp-tools.md)** - Available MCP tools and methods
- **[Configuration](api/configuration.md)** - Configuration options and settings

### Examples
- **[Basic Usage](examples/basic-usage.md)** - Simple parsing examples
- **[Ollama Examples](examples/ollama-examples.md)** - Local AI processing examples
- **[Claude Desktop](examples/claude-desktop.md)** - Integration examples

### Development
- **[Contributing](development/contributing.md)** - How to contribute to the project
- **[Architecture](development/architecture.md)** - System architecture and design
- **[Testing](development/testing.md)** - Testing guidelines and examples

### Legacy Components
- **[Legacy UI](legacy-ui/)** - Historical Streamlit and web UI components (not actively maintained)

## 🚀 Quick Start

### Cloud AI (High Accuracy)
```bash
# Install with cloud AI support
uv pip install 'email-parsing-mcp[ai]'
export GOOGLE_API_KEY="your-key"

# Parse emails
python -m src.email_parser.main --mcp
```

### Local AI with Ollama (Privacy-First)
```bash
# Install Ollama and a model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:1b

# Install email parser
uv pip install 'email-parsing-mcp[ai]'

# Run with local AI
python -m src.email_parser.main --mcp --local
```

### CLI Usage
```bash
# Parse single email
python cli.py parse --file email.msg --local

# Parse folder with Ollama
python cli.py parse-folder --folder emails/ --local --output detailed

# Extract entities from text
python cli.py extract --text "Meeting tomorrow at 2 PM" --local
```

## 💡 Key Features

- **🤖 Dual AI Support**: Cloud (Gemini) and Local (Ollama) AI processing
- **🔒 Privacy-First**: Complete local processing with Ollama
- **⚡ Fast Fallback**: Graceful degradation to regex patterns
- **🔧 MCP Integration**: Full Model Context Protocol support
- **📊 Rich Extraction**: Entities, sentiment, priorities, action items
- **🎯 Source Grounding**: Precise text location mapping

## 🛟 Support

- **Issues**: [GitHub Issues](https://github.com/devraj21/em-ai-lyze/issues)
- **Discussions**: [GitHub Discussions](https://github.com/devraj21/em-ai-lyze/discussions)
- **Documentation**: This docs folder
- **Examples**: See `docs/examples/` for practical use cases