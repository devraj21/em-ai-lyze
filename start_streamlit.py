#!/usr/bin/env python3
"""
Streamlit UI Launcher for Em-AI-lyze
Quick startup script with dependency checking
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} found")
    except ImportError:
        print("❌ Streamlit not found")
        print("Install with: uv pip install streamlit")
        return False
    
    # Check if email parser is available
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    try:
        from email_parser.parser import EmailParser
        print("✅ Email parser available")
    except ImportError as e:
        print(f"❌ Email parser not available: {e}")
        print("Install with: uv pip install -e \".[ai]\"")
        return False
    
    # Check RAG dependencies (optional)
    try:
        from email_parser.rag_cli import RAG_CLI_AVAILABLE
        if RAG_CLI_AVAILABLE:
            print("✅ RAG components available")
        else:
            print("⚠️ RAG components not available (optional)")
            print("Install with: uv pip install \".[rag]\"")
    except ImportError:
        print("⚠️ RAG components not available (optional)")
    
    return True

def find_available_port(start_port=8501):
    """Find an available port starting from start_port"""
    import socket
    
    for port in range(start_port, start_port + 10):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def start_streamlit():
    """Start the Streamlit application"""
    print("🚀 Starting Em-AI-lyze Streamlit UI...")
    
    # Find available port
    port = find_available_port(8501)
    if port is None:
        print("❌ No available ports found in range 8501-8510")
        return False
    
    if port != 8501:
        print(f"📡 Port 8501 is busy, using port {port} instead")
    
    # Set environment variables for better performance
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_GLOBAL_DEVELOPMENT_MODE'] = 'false'
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_ui.py",
            "--server.headless", "false",
            "--server.port", str(port),
            "--theme.base", "light"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Streamlit UI stopped by user")
        return True

def main():
    """Main entry point"""
    print("🤖 Em-AI-lyze Streamlit UI Launcher")
    print("=" * 40)
    
    # Check if streamlit_ui.py exists
    ui_file = Path("streamlit_ui.py")
    if not ui_file.exists():
        print(f"❌ {ui_file} not found in current directory")
        print("Please run this script from the project root directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        return
    
    print("\n🌐 Starting Streamlit UI...")
    print("The web interface will open in your default browser")
    print("URL: http://localhost:8501 (or next available port)")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Start Streamlit
    start_streamlit()

if __name__ == "__main__":
    main()