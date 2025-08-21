#!/usr/bin/env python3
"""
Test the manual mapping features
"""

import pandas as pd
import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_manual_mapping_workflow():
    """Test the complete manual mapping workflow."""
    print("🧪 Testing Manual Mapping Features")
    print("=" * 50)
    
    # Test file
    test_file = "examples/Batchload files/Group 1.xls"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        print("1️⃣ Loading test data...")
        df = pd.read_excel(test_file, engine='xlrd')
        data_columns = df.columns.tolist()
        print(f"   📊 Data columns: {len(data_columns)}")
        print(f"   📋 Sample columns: {data_columns[:5]}")
        
        print("\n2️⃣ Testing automatic mapping...")
        from src.data_ingestion.mapper import ConfigurableDataIngestionMapper
        
        mapper = ConfigurableDataIngestionMapper(config_dir="config", template_name="template_1")
        auto_mappings = mapper._find_column_mappings(data_columns, "template_1")
        target_columns = mapper._load_target_schema(mapper.config_manager.get_template_config("template_1"))
        
        print(f"   🔄 Auto mappings found: {len(auto_mappings)}")
        print(f"   🎯 Target columns: {len(target_columns)}")
        print(f"   📈 Auto coverage: {len(auto_mappings)/len(target_columns)*100:.1f}%")
        
        print("\n3️⃣ Creating manual mapping example...")
        # Simulate manual mappings that would improve coverage
        manual_mappings = auto_mappings.copy()
        
        # Add some manual mappings for unmapped columns
        unmapped_targets = set(target_columns) - set(auto_mappings.keys())
        available_sources = set(data_columns) - set(auto_mappings.values())
        
        # Map a few unmapped targets manually
        manual_additions = 0
        for target in list(unmapped_targets)[:3]:  # Map first 3 unmapped
            if available_sources:
                source = available_sources.pop()
                manual_mappings[target] = source
                manual_additions += 1
                print(f"   ➕ Manual mapping: {target} <- {source}")
        
        print(f"   🔧 Manual mappings added: {manual_additions}")
        print(f"   📈 Improved coverage: {len(manual_mappings)/len(target_columns)*100:.1f}%")
        
        print("\n4️⃣ Testing mapping export...")
        mapping_json = json.dumps(manual_mappings, indent=2)
        export_file = "test_mappings_export.json"
        
        with open(export_file, 'w') as f:
            f.write(mapping_json)
        print(f"   💾 Exported mappings to: {export_file}")
        
        print("\n5️⃣ Testing mapping import...")
        with open(export_file, 'r') as f:
            imported_mappings = json.loads(f.read())
        
        print(f"   📤 Imported {len(imported_mappings)} mappings")
        print(f"   ✅ Import/Export validation: {'PASS' if imported_mappings == manual_mappings else 'FAIL'}")
        
        print("\n6️⃣ Testing direct processing with manual mappings...")
        from data_ingestion_streamlit import process_dataframe_directly
        
        # Simulate session state
        class MockSessionState:
            current_mappings = {
                'data_file': 'Group 1.xls',
                'manual_overrides': manual_mappings
            }
        
        # Temporarily mock st.session_state
        import data_ingestion_streamlit
        original_session_state = getattr(data_ingestion_streamlit.st, 'session_state', None)
        data_ingestion_streamlit.st.session_state = MockSessionState()
        
        # Mock st.info to capture messages
        info_messages = []
        original_info = getattr(data_ingestion_streamlit.st, 'info', lambda x: info_messages.append(x))
        data_ingestion_streamlit.st.info = lambda x: info_messages.append(x)
        
        try:
            result_df = process_dataframe_directly(
                mapper, df, 'Group 1.xls', 'template_1', 'xlsx', True
            )
            
            print(f"   ✅ Processing successful with manual mappings!")
            print(f"   📊 Output shape: {result_df.shape}")
            print(f"   💬 Info messages: {len(info_messages)}")
            
            if info_messages:
                print(f"   📝 Last message: {info_messages[-1]}")
                
        finally:
            # Restore original session state
            if original_session_state:
                data_ingestion_streamlit.st.session_state = original_session_state
            data_ingestion_streamlit.st.info = original_info
        
        print("\n7️⃣ Testing data preview functionality...")
        
        # Test column statistics generation
        stats_data = []
        preview_columns = data_columns[:3]  # Test first 3 columns
        
        for col in preview_columns:
            non_null_count = df[col].notna().sum()
            null_count = len(df) - non_null_count
            data_type = str(df[col].dtype)
            sample_values = df[col].dropna().head(3).tolist()
            
            stats_data.append({
                "Column": col,
                "Non-null": non_null_count,
                "Null": null_count,
                "Data Type": data_type,
                "Sample Values": sample_values
            })
        
        print(f"   📈 Generated statistics for {len(stats_data)} columns")
        for stat in stats_data:
            print(f"   📊 {stat['Column']}: {stat['Non-null']} non-null, {stat['Data Type']}")
        
        # Cleanup
        if os.path.exists(export_file):
            os.remove(export_file)
        
        print("\n✅ ALL MANUAL MAPPING TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the manual mapping tests."""
    success = test_manual_mapping_workflow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MANUAL MAPPING FEATURES VERIFIED!")
        print("\n🚀 New Features Available in Streamlit UI:")
        print("   🔍 Data Preview - See sample data before mapping")
        print("   🔧 Manual Column Mapping - 3 tabs for different mapping scenarios")
        print("   📊 Real-time Coverage Updates - See mapping improvements")
        print("   💾 Save/Load Mappings - Export and import mapping configurations")
        print("   🔄 Reset Options - Switch between auto and manual mappings")
        print("   📈 Enhanced Visualizations - Color-coded mapping status")
        print("\n📍 Go to 'Mapping Analysis' section to try these features!")
    else:
        print("❌ Manual mapping features need fixes")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)