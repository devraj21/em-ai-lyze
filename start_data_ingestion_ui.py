#!/usr/bin/env python3
"""
Startup script for the Configuration-Driven Data Ingestion Mapper Streamlit UI
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    """Start the Streamlit application."""
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if we're in an activated virtual environment
    if sys.prefix != sys.base_prefix:
        # We're in a virtual environment
        python_path = sys.executable
        print("🔧 Using activated virtual environment...")
    else:
        # Check for local venv
        venv_path = script_dir / ".venv"
        if venv_path.exists():
            print("🔧 Using local virtual environment...")
            if sys.platform == "win32":
                python_path = venv_path / "Scripts" / "python.exe"
            else:
                python_path = venv_path / "bin" / "python"
            
            if not python_path.exists():
                print("❌ Virtual environment Python not found. Please run: ./setup.sh")
                return
        else:
            python_path = "python"
            print("⚠️  Virtual environment not found. Using system Python...")
    
    # Start Streamlit
    print("🚀 Starting Data Ingestion Mapper UI...")
    print("📱 Opening in browser: http://localhost:8503")
    print("🔧 To stop the server, press Ctrl+C")
    print("-" * 50)
    
    try:
        cmd = [
            str(python_path),
            "-m", "streamlit", "run",
            "data_ingestion_streamlit.py",
            "--server.port", "8503",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Data Ingestion Mapper UI...")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it:")
        print("   source .venv/bin/activate")
        print("   uv pip install streamlit plotly")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")

if __name__ == "__main__":
    main()