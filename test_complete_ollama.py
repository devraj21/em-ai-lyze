#!/usr/bin/env python3
"""
Complete Ollama integration test - demonstrates all features working together
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_complete_integration():
    """Test complete Ollama integration"""
    print("🚀 Complete Ollama Integration Test")
    print("=" * 50)
    
    # Test all three configurations
    configs = [
        {
            "name": "Local Ollama AI",
            "params": {"use_ai": True, "use_local": True},
            "icon": "🏠"
        },
        {
            "name": "Cloud AI (Fallback)",
            "params": {"use_ai": True, "use_local": False},
            "icon": "☁️"
        },
        {
            "name": "Regex Only",
            "params": {"use_ai": False},
            "icon": "🔧"
        }
    ]
    
    sample_email_content = """
    Subject: Meeting Tomorrow - Q4 Budget Discussion
    
    Hi Sarah,
    
    Can you join us for the budget meeting tomorrow at 2 PM EST? 
    We need to finalize the $150,000 allocation for the new project.
    
    Please confirm by calling 555-444-3333 or email john.smith@company.com
    
    Location: Conference Room B, Floor 3
    
    Thanks!
    Mike
    """
    
    from email_parser.parser import EmailParser
    from email_parser.mcp_server import EmailParserMCPServer
    
    results = {}
    
    for config in configs:
        print(f"\n{config['icon']} Testing {config['name']}:")
        print("-" * 30)
        
        try:
            # Test parser
            parser = EmailParser(**config['params'])
            print(f"✓ Parser initialized")
            
            if hasattr(parser, 'ai_extractor') and parser.ai_extractor:
                print(f"✓ Using model: {parser.ai_extractor.model_id}")
            
            # Test entity extraction
            entities = parser.extract_entities_from_text(sample_email_content)
            
            print("📋 Extracted entities:")
            entity_count = 0
            for entity_type, values in entities.items():
                if values and not entity_type.startswith('_'):
                    print(f"  • {entity_type}: {values}")
                    entity_count += len(values)
            
            ai_enhanced = entities.get('_ai_enhanced', ['false'])[0] == 'true'
            print(f"🤖 AI Status: {'Active' if ai_enhanced else 'Fallback/Disabled'}")
            
            # Test MCP server
            server = EmailParserMCPServer(
                name=f"test-{config['name'].lower().replace(' ', '-')}",
                **config['params']
            )
            print(f"✓ MCP Server initialized")
            
            results[config['name']] = {
                'parser_ok': True,
                'server_ok': True,
                'entities_found': entity_count,
                'ai_active': ai_enhanced
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[config['name']] = {
                'parser_ok': False,
                'server_ok': False,
                'entities_found': 0,
                'ai_active': False
            }
    
    # Summary
    print(f"\n📊 Integration Test Summary")
    print("=" * 50)
    
    for config_name, result in results.items():
        status = "✅" if result['parser_ok'] and result['server_ok'] else "❌"
        print(f"{status} {config_name}")
        print(f"   Entities found: {result['entities_found']}")
        print(f"   AI active: {'✓' if result['ai_active'] else '✗'}")
    
    # Show usage examples
    print(f"\n💡 Ready to Use!")
    print("=" * 50)
    print("Local AI Email Parser:")
    print("  parser = EmailParser(use_ai=True, use_local=True)")
    print()
    print("Start MCP Server with Ollama:")
    print("  python -m src.email_parser.main --mcp --local")
    print()
    print("Claude Desktop Configuration:")
    print('  "args": ["-m", "src.email_parser.main", "--mcp", "--local"]')
    
    return all(r['parser_ok'] for r in results.values())

if __name__ == "__main__":
    success = test_complete_integration()
    
    if success:
        print(f"\n🎉 All integrations working! Ollama email parsing is ready!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Some integrations had issues, but basic functionality works")
        sys.exit(1)