#!/usr/bin/env python3
"""
Quick test to verify .xls file processing fix
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_streamlit_file_reading():
    """Test file reading with the same approach as Streamlit UI."""
    print("🧪 Testing Streamlit .xls File Reading Fix")
    print("=" * 50)
    
    test_file = "examples/Batchload files/Group 1.xls"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Testing file: {test_file}")
    
    try:
        # Test the exact same logic as in the Streamlit UI
        file_extension = os.path.splitext(test_file)[1].lower()
        print(f"🔍 Detected extension: {file_extension}")
        
        if file_extension == '.csv':
            df = pd.read_csv(test_file)
        elif file_extension == '.xls':
            df = pd.read_excel(test_file, engine='xlrd')
            print("✅ Used xlrd engine for .xls file")
        elif file_extension == '.xlsx':
            df = pd.read_excel(test_file, engine='openpyxl')
            print("✅ Used openpyxl engine for .xlsx file")
        else:
            df = pd.read_excel(test_file, engine='openpyxl')
        
        print(f"✅ Successfully read file!")
        print(f"📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"📋 First 5 columns: {list(df.columns[:5])}")
        
        # Test the direct processing approach
        print("\n🔄 Testing direct DataFrame processing...")
        
        from src.data_ingestion.mapper import ConfigurableDataIngestionMapper
        from data_ingestion_streamlit import process_dataframe_directly
        
        mapper = ConfigurableDataIngestionMapper(config_dir="config")
        
        result_df = process_dataframe_directly(
            mapper, df, "Group 1.xls", "template_1", "xlsx", True
        )
        
        print(f"✅ Direct processing successful!")
        print(f"📊 Output shape: {result_df.shape[0]} rows × {result_df.shape[1]} columns")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    success = test_streamlit_file_reading()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 XLS File Processing Fix VERIFIED!")
        print("✅ The Streamlit UI should now handle .xls files correctly")
        print("\n🚀 Try uploading Group 1.xls in the Streamlit interface")
    else:
        print("❌ Fix verification failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)