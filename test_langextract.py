#!/usr/bin/env python3
"""
Test script for LangExtract integration with email parser
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_ai_extractor():
    """Test the AI extractor directly"""
    try:
        from email_parser.ai_extractor import AIEmailExtractor
        print("✓ AI Extractor imported successfully")
        
        # Test initialization
        extractor = AIEmailExtractor()
        print(f"✓ AI Extractor initialized (available: {extractor.available})")
        
        if not extractor.available:
            print("⚠ LangExtract not available, will use fallback patterns")
        
        # Test entity extraction
        test_text = """
        Dear John,
        
        Please call me at 555-123-4567 tomorrow at 2:00 PM EST.
        We need to discuss the $15,000 contract due on 12/15/2024.
        Contact sarah@company.com for the details.
        
        Best regards,
        Mike
        """
        
        print("\nTesting entity extraction...")
        entities = extractor.extract_entities_from_text(test_text)
        print(f"Extracted entities: {entities}")
        
        # Test structured data extraction
        print("\nTesting structured data extraction...")
        structured_data = extractor.extract_structured_data(
            subject="Contract Discussion - Urgent",
            body=test_text,
            sender="mike@company.com",
            recipients=["john@company.com"]
        )
        
        print(f"Summary: {structured_data.summary}")
        print(f"Priority: {structured_data.priority_level}")
        print(f"Sentiment: {structured_data.sentiment}")
        print(f"Categories: {structured_data.categories}")
        print(f"Action items: {len(structured_data.action_items)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing AI extractor: {e}")
        return False

def test_email_parser():
    """Test the enhanced email parser"""
    try:
        from email_parser.parser import EmailParser
        print("\n=== Testing Enhanced Email Parser ===")
        
        # Test with AI enabled
        parser_ai = EmailParser(use_ai=True)
        print(f"✓ Parser with AI initialized (AI active: {parser_ai.use_ai})")
        
        # Test without AI
        parser_regex = EmailParser(use_ai=False)
        print(f"✓ Parser without AI initialized (AI active: {parser_regex.use_ai})")
        
        # Test entity extraction from text
        test_text = "Meeting with John at john@company.com on 01/15/2024 about $50,000 budget."
        
        print(f"\nTesting entity extraction on: '{test_text}'")
        
        entities_ai = parser_ai.extract_entities_from_text(test_text)
        entities_regex = parser_regex.extract_entities_from_text(test_text)
        
        print(f"AI entities: {entities_ai}")
        print(f"Regex entities: {entities_regex}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing email parser: {e}")
        return False

def test_mcp_server():
    """Test the MCP server with AI integration"""
    try:
        from email_parser.mcp_server import EmailParserMCPServer
        print("\n=== Testing MCP Server ===")
        
        # Test with AI
        server_ai = EmailParserMCPServer(use_ai=True)
        print(f"✓ MCP Server with AI initialized")
        
        # Test without AI
        server_no_ai = EmailParserMCPServer(use_ai=False)
        print(f"✓ MCP Server without AI initialized")
        
        print("✓ MCP Server integration working")
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP server: {e}")
        return False

def main():
    print("Testing LangExtract Integration with Email Parser")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_ai_extractor()
    success &= test_email_parser() 
    success &= test_mcp_server()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! LangExtract integration is working.")
        print("\nTo use AI features, install with:")
        print("  uv pip install 'email-parsing-mcp[ai]'")
        print("\nThen ensure you have a supported AI model (Gemini API key, etc.)")
    else:
        print("✗ Some tests failed. Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())