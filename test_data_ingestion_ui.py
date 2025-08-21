#!/usr/bin/env python3
"""
Test script for the Data Ingestion Mapper functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_functionality():
    """Test basic functionality of the data ingestion mapper."""
    print("🧪 Testing Data Ingestion Mapper Basic Functionality")
    print("=" * 60)
    
    try:
        # Test imports
        print("1️⃣ Testing imports...")
        from src.data_ingestion.mapper import ConfigurableDataIngestionMapper
        from src.data_ingestion.config_manager import ConfigurationManager
        print("✅ Core modules imported successfully")
        
        # Test configuration loading
        print("\n2️⃣ Testing configuration loading...")
        config_manager = ConfigurationManager("config")
        templates = config_manager.get_available_templates()
        print(f"✅ Found {len(templates)} templates: {templates}")
        
        # Test mapper initialization
        print("\n3️⃣ Testing mapper initialization...")
        mapper = ConfigurableDataIngestionMapper(config_dir="config")
        print("✅ Mapper initialized successfully")
        
        # Test template resolution
        print("\n4️⃣ Testing template resolution...")
        test_files = [
            "examples/Batchload files/Group 1.xls",
            "examples/Change files/AON.xls"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                template = config_manager.resolve_file_template(test_file)
                print(f"✅ {os.path.basename(test_file)} → {template}")
            else:
                print(f"⚠️  {test_file} not found")
        
        # Test mapping report generation
        print("\n5️⃣ Testing mapping report generation...")
        report = mapper.generate_mapping_report("examples/Batchload files")
        report_lines = report.split('\n')
        print(f"✅ Generated mapping report ({len(report_lines)} lines)")
        print("📋 Sample report preview:")
        for line in report_lines[:10]:
            print(f"   {line}")
        if len(report_lines) > 10:
            print("   ...")
        
        print(f"\n🎉 All basic functionality tests passed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_file_processing():
    """Test actual file processing functionality."""
    print("\n\n🔬 Testing File Processing")
    print("=" * 60)
    
    try:
        from src.data_ingestion.mapper import ConfigurableDataIngestionMapper
        
        # Test with a real file
        test_file = "examples/Batchload files/Group 2.csv"
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            return True
        
        print(f"1️⃣ Processing test file: {test_file}")
        mapper = ConfigurableDataIngestionMapper(config_dir="config")
        
        # Process file
        result_df = mapper.process_file(test_file)
        print(f"✅ Processed successfully!")
        print(f"📊 Result shape: {result_df.shape[0]} rows × {result_df.shape[1]} columns")
        
        # Show sample columns
        print("📋 Sample output columns:")
        for i, col in enumerate(result_df.columns[:10]):
            print(f"   {i+1:2d}. {col}")
        if len(result_df.columns) > 10:
            print(f"   ... and {len(result_df.columns) - 10} more columns")
        
        print("\n🎉 File processing test passed!")
        
    except Exception as e:
        print(f"❌ Error during file processing test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_ui_dependencies():
    """Test UI-specific dependencies."""
    print("\n\n🎨 Testing UI Dependencies")
    print("=" * 60)
    
    try:
        print("1️⃣ Testing Streamlit...")
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        print("2️⃣ Testing Plotly...")
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Plotly imported successfully")
        
        print("3️⃣ Testing Pandas...")
        import pandas as pd
        test_df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        print(f"✅ Pandas working (test dataframe: {test_df.shape})")
        
        print("\n🎉 All UI dependencies available!")
        
    except Exception as e:
        print(f"❌ UI dependency error: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Data Ingestion Mapper - Test Suite")
    print("=" * 80)
    
    # Ensure we're in the correct directory
    os.chdir(project_root)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_basic_functionality()
    all_passed &= test_file_processing()
    all_passed &= test_ui_dependencies()
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The Data Ingestion Mapper is ready to use.")
        print("\n🚀 To start the Streamlit UI, run:")
        print("   python start_data_ingestion_ui.py")
        print("\n   or manually:")
        print("   source .venv/bin/activate")
        print("   streamlit run data_ingestion_streamlit.py")
    else:
        print("❌ Some tests failed. Please check the configuration and dependencies.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)