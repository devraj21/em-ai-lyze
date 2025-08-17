#!/usr/bin/env python3
"""
Launcher script for FastAPI Web UI
Starts the web interface for email parsing and data ingestion
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Launch the FastAPI Web UI"""
    try:
        from web_ui import start_web_ui
        
        import argparse
        parser = argparse.ArgumentParser(description="Email Parser & Data Ingestion Web UI")
        parser.add_argument("--host", default="localhost", help="Host to bind to")
        parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
        
        args = parser.parse_args()
        
        print("🚀 Starting FastAPI Web UI")
        print(f"📍 Server URL: http://{args.host}:{args.port}")
        print("📧 Email Parser and Data Ingestion interface")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        asyncio.run(start_web_ui(args.host, args.port))
        
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project root directory and have activated the virtual environment")
        print("💡 Run: source .venv/bin/activate")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting Web UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()