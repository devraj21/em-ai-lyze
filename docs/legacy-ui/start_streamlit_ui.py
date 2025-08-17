#!/usr/bin/env python3
"""
Launcher script for Streamlit UI
Starts the Streamlit interface for email parsing and data ingestion
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit UI"""
    # Path to the Streamlit app in src folder
    app_path = Path(__file__).parent / "src" / "streamlit_ui.py"
    
    if not app_path.exists():
        print(f"❌ Streamlit app not found at: {app_path}")
        print("💡 Make sure you're in the project root directory")
        sys.exit(1)
    
    print("🎈 Starting Streamlit UI")
    print("📍 The app will open in your default browser at: http://localhost:8501")
    print("📧 Email Parser and Data Ingestion interface")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        # Launch Streamlit with the app from src folder
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.serverAddress", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit UI stopped")
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: uv pip install streamlit")
        print("💡 Make sure you have activated the virtual environment")
        print("💡 Run: source .venv/bin/activate")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()