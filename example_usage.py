#!/usr/bin/env python3
"""
Example usage of LangExtract integration with email parser
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_ai_parsing():
    """Demonstrate AI-powered email parsing capabilities"""
    from email_parser.parser import EmailParser
    
    print("🤖 LangExtract Email Parser Integration Demo")
    print("=" * 50)
    
    # Initialize parser with AI
    print("Initializing parser with AI capabilities...")
    parser = EmailParser(use_ai=True, ai_model="gemini-1.5-flash")
    print(f"✓ Parser initialized (AI active: {parser.use_ai})")
    
    # Test with sample email content
    sample_text = """
    Subject: Urgent: Q4 Budget Meeting Tomorrow
    
    Hi team,
    
    We need to meet tomorrow at 2:00 PM EST in Conference Room B to finalize our Q4 budget.
    Please bring your department's spending reports and projections. The board deadline 
    is December 20th, 2024, so we can't delay this any further.
    
    Action items for the meeting:
    1. Review current spending vs. budget
    2. Approve additional $50,000 for marketing initiatives
    3. Discuss 2025 planning timeline
    
    If you can't attend, please contact Sarah Johnson at 555-123-4567 or 
    sarah.johnson@company.com by end of day.
    
    Thanks,
    Mike Rodriguez
    Director of Finance
    """
    
    print("\n📧 Sample Email Content:")
    print("-" * 30)
    print(sample_text[:200] + "...")
    
    print("\n🔍 Extracting entities with AI...")
    entities = parser.extract_entities_from_text(sample_text)
    
    print("📋 Extracted Entities:")
    for entity_type, values in entities.items():
        if values and not entity_type.startswith('_'):
            print(f"  • {entity_type.title()}: {values}")
    
    # Demonstrate AI enhancement indicator
    if '_ai_enhanced' in entities:
        ai_used = entities['_ai_enhanced'][0] == 'true'
        print(f"\n🤖 AI Enhancement: {'✓ Active' if ai_used else '✗ Fallback mode'}")
    
    print("\n" + "=" * 50)
    print("Demo completed! Install langextract and set GOOGLE_API_KEY for full AI features.")

def demo_mcp_server():
    """Demonstrate MCP server with AI integration"""
    from email_parser.mcp_server import EmailParserMCPServer
    
    print("\n🔗 MCP Server Integration Demo")
    print("=" * 50)
    
    # Initialize MCP servers
    print("Initializing MCP servers...")
    
    server_with_ai = EmailParserMCPServer(name="email-parser-ai", use_ai=True)
    server_without_ai = EmailParserMCPServer(name="email-parser-basic", use_ai=False)
    
    print("✓ MCP Server with AI initialized")
    print("✓ MCP Server without AI initialized")
    
    print("\n🛠️ Available tools:")
    print("  • parse_email_file() - Parse .msg files with AI enhancement")
    print("  • parse_email_folder() - Batch process email folders")
    print("  • analyze_email_patterns() - Pattern analysis across emails")
    print("  • extract_entities_from_text() - AI-powered entity extraction")
    
    print("\n📡 Integration methods:")
    print("  • Claude Desktop via stdio transport")
    print("  • HTTP API via REST endpoints")
    print("  • WebSocket for real-time communication")
    print("  • Direct Python import")

if __name__ == "__main__":
    try:
        demo_ai_parsing()
        demo_mcp_server()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Note: This is expected if AI dependencies aren't fully configured")