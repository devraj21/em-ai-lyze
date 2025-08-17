#!/usr/bin/env python3
"""
Test Ollama integration with the email parser
"""

import sys
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_ollama_available():
    """Check if Ollama is available and list models"""
    print("🔍 Checking Ollama availability...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ Ollama is available!")
            print("\n📋 Available models:")
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines:
                    print(f"  {line}")
                return True
            else:
                print("  No models found. You may need to pull a model first.")
                print("  Try: ollama pull llama3.2:1b")
                return False
        else:
            print("✗ Ollama command failed")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ Ollama not found. Please install Ollama first.")
        print("  Visit: https://ollama.ai")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False

def test_ollama_parser():
    """Test the email parser with Ollama"""
    print("\n🤖 Testing Email Parser with Ollama...")
    
    try:
        from email_parser.parser import EmailParser
        
        # Test with local Ollama
        print("Initializing parser with local Ollama...")
        parser = EmailParser(use_ai=True, use_local=True)
        
        print(f"✓ Parser initialized")
        print(f"  - AI enabled: {parser.use_ai}")
        print(f"  - Using local: {parser.use_local}")
        if parser.ai_extractor:
            print(f"  - Model: {parser.ai_extractor.model_id}")
        
        # Test entity extraction
        test_text = """
        Hi team,
        
        Let's meet tomorrow at 3 PM in Conference Room A to discuss the $25,000 budget for Q4.
        Contact Sarah at sarah@company.com or 555-987-6543 if you can't make it.
        
        Thanks,
        Mike
        """
        
        print(f"\n📝 Testing entity extraction...")
        entities = parser.extract_entities_from_text(test_text)
        
        print("📋 Extracted entities:")
        for entity_type, values in entities.items():
            if values and not entity_type.startswith('_'):
                print(f"  • {entity_type}: {values}")
        
        # Check if AI was actually used
        if '_ai_enhanced' in entities:
            ai_used = entities['_ai_enhanced'][0] == 'true'
            print(f"\n🔧 AI Enhancement: {'✓ Ollama used' if ai_used else '✗ Fallback to regex'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing parser: {e}")
        return False

def test_mcp_server_ollama():
    """Test MCP server with Ollama"""
    print("\n🔗 Testing MCP Server with Ollama...")
    
    try:
        from email_parser.mcp_server import EmailParserMCPServer
        
        # Initialize with Ollama
        server = EmailParserMCPServer(
            name="email-parser-ollama",
            use_ai=True,
            use_local=True
        )
        
        print("✓ MCP Server with Ollama initialized")
        print(f"  - AI enabled: {server.use_ai}")
        print(f"  - Using local: {server.use_local}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP server: {e}")
        return False

def recommend_models():
    """Recommend good Ollama models for email parsing"""
    print("\n💡 Recommended Ollama models for email parsing:")
    print("=" * 50)
    
    models = [
        {
            "name": "llama3.2:1b",
            "size": "~1GB",
            "description": "Small, fast model good for entity extraction",
            "command": "ollama pull llama3.2:1b"
        },
        {
            "name": "llama3.2:latest",
            "size": "~2GB", 
            "description": "Balanced model with good accuracy",
            "command": "ollama pull llama3.2:latest"
        },
        {
            "name": "phi3:mini",
            "size": "~2.3GB",
            "description": "Microsoft's efficient model, good for structured tasks",
            "command": "ollama pull phi3:mini"
        },
        {
            "name": "mistral:latest",
            "size": "~4GB",
            "description": "High-quality model for complex extraction",
            "command": "ollama pull mistral:latest"
        }
    ]
    
    for model in models:
        print(f"📦 {model['name']} ({model['size']})")
        print(f"   {model['description']}")
        print(f"   Install: {model['command']}")
        print()

def main():
    print("🚀 Ollama Integration Test for Email Parser")
    print("=" * 50)
    
    # Check Ollama availability
    ollama_available = check_ollama_available()
    
    if ollama_available:
        # Test parser
        parser_success = test_ollama_parser()
        
        # Test MCP server  
        server_success = test_mcp_server_ollama()
        
        print("\n" + "=" * 50)
        if parser_success and server_success:
            print("✅ Ollama integration working perfectly!")
            print("\n🎯 You can now use local AI for email parsing:")
            print("   parser = EmailParser(use_ai=True, use_local=True)")
        else:
            print("⚠️ Ollama integration has some issues")
    else:
        recommend_models()
        print("\n📚 Next steps:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Pull a recommended model (see above)")
        print("3. Run this test again")

if __name__ == "__main__":
    main()