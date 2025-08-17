# Legacy UI Components

This folder contains legacy user interface components that were part of the email parser project. These files have been moved here for reference and historical purposes.

## 📁 Contents

### Documentation Files
- **`QUICK_START.md`** - Legacy quick start guide for UI components
- **`STREAMLIT_UI_GUIDE.md`** - Guide for the Streamlit web interface
- **`UI_LAUNCH_GUIDE.md`** - Instructions for launching the web UI

### Python Files
- **`streamlit_ui.py`** - Streamlit web application for email parsing
- **`web_ui.py`** - Alternative web UI implementation  
- **`start_streamlit_ui.py`** - Launcher script for Streamlit UI
- **`start_web_ui.py`** - Launcher script for web UI

## 🎯 Current Approach

The email parser now focuses on:

1. **CLI Interface** - Primary user interface via `cli.py`
2. **MCP Server** - Integration with Claude Desktop
3. **HTTP/WebSocket APIs** - Network transport for integrations
4. **Python API** - Direct programmatic access

## 🔄 Migration Path

If you need web UI functionality, consider:

1. **Modern Web Framework**: Build a new UI using React, Vue, or modern web technologies
2. **API Integration**: Use the HTTP API endpoints from `src/email_parser/transports.py`
3. **MCP Integration**: Integrate with Claude Desktop for interactive analysis
4. **CLI Automation**: Use the CLI with shell scripts for automated processing

## 📋 Legacy UI Features

The legacy UI components provided:

- Web-based email file upload and parsing
- Visual display of extracted entities and analysis
- Interactive email content exploration
- Batch processing with progress tracking
- Results export and visualization

## ⚠️ Status

These files are **legacy components** and are not actively maintained. They may:

- Have outdated dependencies
- Not work with the current parser implementation
- Lack the latest AI integration features
- Require significant updates to function properly

## 🚀 Recommended Alternatives

Instead of using these legacy components, we recommend:

### For Interactive Use
```bash
# Use the CLI with different output formats
python cli.py parse --file email.msg --local --output detailed
python cli.py parse-folder --folder emails/ --local --output json
```

### For Web Integration
```bash
# Start HTTP API server
python -m src.email_parser.transports --transport http --port 8000

# Use REST API endpoints
curl -X POST http://localhost:8000/api/parse/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "./email.msg"}'
```

### For Claude Desktop
```json
{
  "mcpServers": {
    "email-parser": {
      "command": "python",
      "args": ["-m", "src.email_parser.main", "--mcp", "--local"],
      "cwd": "/path/to/email-parser"
    }
  }
}
```

---

For current documentation and usage guides, see the main [docs/](../) folder.