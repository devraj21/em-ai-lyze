"""
Main module for Email Parsing MCP Server
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from .parser import EmailParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_parser.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_mcp_server(use_local=False, ai_model="gemini-1.5-flash"):
    """Run the MCP server"""
    try:
        from .mcp_server import EmailParserMCPServer
        model_type = "local" if use_local else "cloud"
        logger.info(f"Starting Email Parser MCP Server with {model_type} AI...")
        
        # Create and run server
        server = EmailParserMCPServer(
            name="email-parser",
            use_ai=True,
            ai_model=ai_model,
            use_local=use_local
        )
        
        # Run the server
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except ImportError:
            # uvloop is optional, fall back to default event loop
            pass
        
        server.mcp.run()
        
    except ImportError as e:
        logger.error(f"MCP server dependencies not available: {e}")
        logger.info("Install with: uv pip install fastmcp")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)

async def demo_parser():
    """Demonstrate parser functionality"""
    logger.info("Email Parser Demo Mode")
    
    parser = EmailParser()
    logger.info("Email parser initialized successfully")
    
    print("Email Parsing MCP Server - Demo Mode")
    print("===================================")
    print("Parser ready for demonstration.")
    print()
    print("Available commands:")
    print("  python -m src.email_parser.main --mcp    # Start MCP server")
    print("  python -m src.email_parser.main --demo   # Demo mode (current)")
    print("  python cli.py test                       # Test CLI")
    print()
    print("To use MCP server:")
    print("1. Install dependencies: uv pip install fastmcp")
    print("2. Add .msg files to examples/sample_emails/")
    print("3. Connect via Claude Desktop or other MCP client")

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Email Parsing MCP Server")
    parser.add_argument(
        "--mcp", 
        action="store_true", 
        help="Start MCP server (requires fastmcp)"
    )
    parser.add_argument(
        "--demo", 
        action="store_true", 
        help="Run in demo mode (default)"
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        help="MCP transport protocol (stdio, websocket, http)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local Ollama models instead of cloud AI"
    )
    parser.add_argument(
        "--model",
        default="gemini-1.5-flash",
        help="AI model to use (default: gemini-1.5-flash)"
    )
    
    args = parser.parse_args()
    
    if args.mcp:
        run_mcp_server(use_local=args.local, ai_model=args.model)
    else:
        asyncio.run(demo_parser())

if __name__ == "__main__":
    main()
