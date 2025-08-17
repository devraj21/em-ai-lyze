#!/usr/bin/env python3
"""
Example usage of Ollama integration for local AI-powered email parsing
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_ollama_vs_cloud():
    """Compare local Ollama vs cloud AI for email parsing"""
    from email_parser.parser import EmailParser
    
    print("🔄 Ollama vs Cloud AI Comparison")
    print("=" * 50)
    
    sample_email = """
    Subject: URGENT: Budget Approval Needed - Deadline Tomorrow!
    
    Hi Finance Team,
    
    We urgently need approval for the additional $50,000 marketing budget for Q4.
    The board meeting is scheduled for tomorrow (December 15th, 2024) at 2:00 PM EST
    in the main conference room.
    
    Action items:
    1. Review the attached budget proposal
    2. Get approval from Sarah Johnson (CFO) at sarah.johnson@company.com
    3. Confirm attendance by calling 555-123-4567
    
    This is critical for our product launch in January 2025.
    
    Best regards,
    Mike Rodriguez
    Director of Marketing
    """
    
    print("📧 Sample Email:")
    print(sample_email[:200] + "...\n")
    
    # Test with Ollama (local)
    print("🏠 LOCAL PARSING (Ollama):")
    print("-" * 30)
    try:
        parser_local = EmailParser(use_ai=True, use_local=True)
        print(f"✓ Using model: {parser_local.ai_extractor.model_id}")
        
        entities_local = parser_local.extract_entities_from_text(sample_email)
        
        print("📋 Extracted entities:")
        for entity_type, values in entities_local.items():
            if values and not entity_type.startswith('_'):
                print(f"  • {entity_type}: {values}")
        
        ai_used = entities_local.get('_ai_enhanced', ['false'])[0] == 'true'
        print(f"🤖 AI Status: {'✓ Active' if ai_used else '✗ Fallback'}")
        
    except Exception as e:
        print(f"❌ Local parsing error: {e}")
    
    print("\n☁️ CLOUD PARSING (Gemini - requires API key):")
    print("-" * 30)
    try:
        parser_cloud = EmailParser(use_ai=True, use_local=False)
        entities_cloud = parser_cloud.extract_entities_from_text(sample_email)
        
        print("📋 Extracted entities:")
        for entity_type, values in entities_cloud.items():
            if values and not entity_type.startswith('_'):
                print(f"  • {entity_type}: {values}")
        
        ai_used = entities_cloud.get('_ai_enhanced', ['false'])[0] == 'true'
        print(f"🤖 AI Status: {'✓ Active' if ai_used else '✗ Fallback (no API key)'}")
        
    except Exception as e:
        print(f"❌ Cloud parsing error: {e}")

def demo_mcp_server_configs():
    """Show different MCP server configuration options"""
    print("\n🔗 MCP Server Configuration Options")
    print("=" * 50)
    
    from email_parser.mcp_server import EmailParserMCPServer
    
    configs = [
        {
            "name": "Local Ollama",
            "params": {"use_ai": True, "use_local": True},
            "description": "Fast local processing, no API costs"
        },
        {
            "name": "Cloud AI",
            "params": {"use_ai": True, "use_local": False, "ai_model": "gemini-1.5-flash"},
            "description": "High accuracy, requires API key"
        },
        {
            "name": "Regex Only",
            "params": {"use_ai": False},
            "description": "Basic patterns, no AI dependencies"
        }
    ]
    
    for config in configs:
        print(f"\n📡 {config['name']}:")
        print(f"   {config['description']}")
        
        try:
            server = EmailParserMCPServer(
                name=f"email-parser-{config['name'].lower().replace(' ', '-')}",
                **config['params']
            )
            
            print(f"   ✓ Server initialized successfully")
            print(f"   ✓ AI enabled: {server.use_ai}")
            if hasattr(server, 'use_local'):
                print(f"   ✓ Local model: {server.use_local}")
            
        except Exception as e:
            print(f"   ❌ Failed to initialize: {e}")

def show_usage_examples():
    """Show practical usage examples"""
    print("\n💡 Practical Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "Local AI Email Parser",
            "code": """
# Initialize with local Ollama
parser = EmailParser(use_ai=True, use_local=True)

# Parse email file
email_data = parser.parse_msg_file(Path("important.msg"))
print(f"Summary: {email_data.ai_summary}")
print(f"Priority: {email_data.ai_priority}")
print(f"Sentiment: {email_data.sentiment}")
"""
        },
        {
            "title": "MCP Server with Ollama",
            "code": """
# Start MCP server with local AI
server = EmailParserMCPServer(
    name="local-email-parser",
    use_ai=True,
    use_local=True
)

# For Claude Desktop config:
{
  "mcpServers": {
    "email-parser": {
      "command": "python",
      "args": ["-m", "src.email_parser.main", "--mcp", "--local"],
      "cwd": "/path/to/email-parser"
    }
  }
}
"""
        },
        {
            "title": "Entity Extraction",
            "code": """
# Extract entities from any text
text = "Meeting with John at 3 PM about $10k budget"
entities = parser.extract_entities_from_text(text)

# Results with local AI:
# {'people': ['John'], 'money': ['$10k'], 'dates': ['3 PM']}
"""
        }
    ]
    
    for example in examples:
        print(f"\n🔧 {example['title']}:")
        print(example['code'])

def show_model_recommendations():
    """Show recommended Ollama models"""
    print("\n🎯 Recommended Ollama Models for Email Parsing")
    print("=" * 50)
    
    models = [
        {
            "name": "llama3.2:1b",
            "pros": ["Very fast", "Low memory usage (1.3GB)", "Good for basic extraction"],
            "cons": ["Lower accuracy for complex tasks"],
            "best_for": "High-volume processing, resource-constrained environments"
        },
        {
            "name": "phi3:mini", 
            "pros": ["Excellent for structured tasks", "Good accuracy", "Moderate size (2.2GB)"],
            "cons": ["Slightly slower than llama3.2:1b"],
            "best_for": "Balanced performance, business emails"
        },
        {
            "name": "llama3.1:latest",
            "pros": ["High accuracy", "Excellent reasoning", "Good with complex emails"],
            "cons": ["Larger size (~4GB)", "Slower processing"],
            "best_for": "Complex analysis, when accuracy is critical"
        }
    ]
    
    for model in models:
        print(f"\n📦 {model['name']}:")
        print(f"   Best for: {model['best_for']}")
        print(f"   Pros: {', '.join(model['pros'])}")
        print(f"   Cons: {', '.join(model['cons'])}")
        print(f"   Install: ollama pull {model['name']}")

def main():
    print("🚀 Ollama Integration Demo for Email Parser")
    print("Local AI-Powered Email Analysis")
    print("=" * 50)
    
    try:
        demo_ollama_vs_cloud()
        demo_mcp_server_configs()
        show_usage_examples()
        show_model_recommendations()
        
        print(f"\n🎉 Demo completed!")
        print(f"\n📚 Next steps:")
        print(f"1. Choose your preferred Ollama model")
        print(f"2. Use EmailParser(use_ai=True, use_local=True)")
        print(f"3. Enjoy local AI email parsing!")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

if __name__ == "__main__":
    main()