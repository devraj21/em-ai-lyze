#!/usr/bin/env python3
"""
Configuration-Driven Data Ingestion Mapper - Streamlit Interface

This Streamlit application provides a user-friendly interface for the 
configuration-driven data ingestion mapper. Users can upload template files,
upload data files (groups/change files), and visualize the mapping process.
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from pathlib import Path
import traceback
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from io import StringIO

# Import the existing mapper
try:
    from src.data_ingestion.mapper import ConfigurableDataIngestionMapper
    from src.data_ingestion.config_manager import ConfigurationManager
except ImportError:
    st.error("Failed to import data ingestion modules. Please ensure the project is properly set up.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Data Ingestion Mapper",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #A23B72;
        border-bottom: 2px solid #F18F01;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background: linear-gradient(135deg, rgba(46, 134, 171, 0.1), rgba(46, 134, 171, 0.05));
        border: 1px solid rgba(46, 134, 171, 0.3);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #2E86AB;
        margin: 1.5rem 0;
        color: var(--text-color, #333);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.05));
        border: 1px solid rgba(40, 167, 69, 0.3);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #28a745;
        margin: 1.5rem 0;
        color: var(--text-color, #333);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05));
        border: 1px solid rgba(255, 193, 7, 0.3);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #ffc107;
        margin: 1.5rem 0;
        color: var(--text-color, #333);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-box {
        background: linear-gradient(135deg, rgba(220, 53, 69, 0.1), rgba(220, 53, 69, 0.05));
        border: 1px solid rgba(220, 53, 69, 0.3);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #dc3545;
        margin: 1.5rem 0;
        color: var(--text-color, #333);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Dark theme compatibility */
    @media (prefers-color-scheme: dark) {
        .info-box, .success-box, .warning-box, .error-box {
            color: #fff !important;
        }
        .info-box {
            background: linear-gradient(135deg, rgba(46, 134, 171, 0.2), rgba(46, 134, 171, 0.1));
        }
        .success-box {
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.2), rgba(40, 167, 69, 0.1));
        }
        .warning-box {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
        }
        .error-box {
            background: linear-gradient(135deg, rgba(220, 53, 69, 0.2), rgba(220, 53, 69, 0.1));
        }
    }
    /* Streamlit dark theme detection */
    .stApp[data-theme="dark"] .info-box,
    .stApp[data-theme="dark"] .success-box,
    .stApp[data-theme="dark"] .warning-box,
    .stApp[data-theme="dark"] .error-box {
        color: #fff !important;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    if 'current_mappings' not in st.session_state:
        st.session_state.current_mappings = {}
    if 'template_files' not in st.session_state:
        st.session_state.template_files = {}
    if 'data_files' not in st.session_state:
        st.session_state.data_files = {}
    if 'mapper' not in st.session_state:
        st.session_state.mapper = None

@st.cache_data
def load_existing_templates():
    """Load existing template configurations."""
    try:
        config_manager = ConfigurationManager("config")
        templates = config_manager.get_available_templates()
        template_configs = {}
        
        for template_name in templates:
            config = config_manager.get_template_config(template_name)
            if config:
                template_configs[template_name] = config
        
        return template_configs
    except Exception as e:
        st.error(f"Error loading existing templates: {e}")
        return {}

def display_template_info(template_configs: Dict[str, Any]):
    """Display information about available templates."""
    st.markdown('<div class="section-header">📋 Available Templates</div>', unsafe_allow_html=True)
    
    if not template_configs:
        st.warning("No templates found in configuration.")
        return
    
    for template_name, config in template_configs.items():
        with st.expander(f"📄 {config.get('name', template_name)}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Template ID:**", template_name)
                st.write("**Description:**", config.get('description', 'No description'))
                st.write("**Template File:**", config.get('template_file', 'Not specified'))
                
            with col2:
                st.write("**Sheet Name:**", config.get('sheet_name', 'Default'))
                st.write("**Header Row:**", config.get('header_row', 0))
                st.write("**Date Format:**", config.get('data_transformations', {}).get('date_format', 'DD/MM/YYYY'))
            
            # Show sample column mappings
            if 'column_mappings' in config:
                st.write("**Sample Column Mappings:**")
                sample_mappings = {}
                for category, mappings in config.get('column_mappings', {}).items():
                    if isinstance(mappings, dict):
                        for target, sources in list(mappings.items())[:3]:  # Show first 3
                            if isinstance(sources, list) and sources:
                                sample_mappings[target] = sources[0] if sources else "N/A"
                
                if sample_mappings:
                    df_mappings = pd.DataFrame([
                        {"Target Column": k, "Sample Source": v} 
                        for k, v in sample_mappings.items()
                    ])
                    st.dataframe(df_mappings, use_container_width=True)

def upload_template_files():
    """Handle template file uploads."""
    st.markdown('<div class="section-header">📁 Upload Template Files</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>Template Files:</strong> These define the target schema for your data mapping.
        Upload Excel/CSV files that represent your desired output format.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_templates = st.file_uploader(
        "Choose template files",
        accept_multiple_files=True,
        type=['xlsx', 'xls', 'csv'],
        key="template_uploader"
    )
    
    if uploaded_templates:
        for template_file in uploaded_templates:
            file_name = template_file.name
            
            try:
                # Read and preview the template with proper engine specification
                file_extension = os.path.splitext(file_name)[1].lower()
                
                if file_extension == '.csv':
                    df = pd.read_csv(template_file)
                elif file_extension == '.xls':
                    df = pd.read_excel(template_file, engine='xlrd')
                elif file_extension == '.xlsx':
                    df = pd.read_excel(template_file, engine='openpyxl')
                else:
                    # Default to openpyxl for unknown extensions
                    df = pd.read_excel(template_file, engine='openpyxl')
                
                st.session_state.template_files[file_name] = {
                    'dataframe': df,
                    'file_obj': template_file,
                    'columns': df.columns.tolist(),
                    'shape': df.shape
                }
                
                with st.expander(f"📊 Preview: {file_name}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
                    with col2:
                        st.write(f"**File Size:** {template_file.size} bytes")
                    
                    st.write("**Columns:**")
                    cols_per_row = 3
                    for i in range(0, len(df.columns), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col_name in enumerate(df.columns[i:i+cols_per_row]):
                            with cols[j]:
                                st.write(f"• {col_name}")
                    
                    st.write("**Sample Data:**")
                    st.dataframe(df.head(3), use_container_width=True)
            
            except Exception as e:
                st.error(f"Error reading template file {file_name}: {e}")

def upload_data_files():
    """Handle data file uploads."""
    st.markdown('<div class="section-header">📊 Upload Data Files</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>Data Files:</strong> These are your source files that need to be mapped to templates.
        Upload group files, change files, or any data files you want to process.
        <br><br>
        <strong>Supported Formats:</strong><br>
        📄 CSV files (.csv)<br>
        📊 Excel files (.xlsx, .xls) - Both new and legacy formats supported<br>
        📈 Multiple sheets supported (configurable per template)
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_data_files = st.file_uploader(
        "Choose data files",
        accept_multiple_files=True,
        type=['xlsx', 'xls', 'csv'],
        key="data_uploader"
    )
    
    if uploaded_data_files:
        for data_file in uploaded_data_files:
            file_name = data_file.name
            
            try:
                # Read and preview the data file with proper engine specification
                file_extension = os.path.splitext(file_name)[1].lower()
                
                if file_extension == '.csv':
                    df = pd.read_csv(data_file)
                elif file_extension == '.xls':
                    df = pd.read_excel(data_file, engine='xlrd')
                elif file_extension == '.xlsx':
                    df = pd.read_excel(data_file, engine='openpyxl')
                else:
                    # Default to openpyxl for unknown extensions
                    df = pd.read_excel(data_file, engine='openpyxl')
                
                st.session_state.data_files[file_name] = {
                    'dataframe': df,
                    'file_obj': data_file,
                    'columns': df.columns.tolist(),
                    'shape': df.shape,
                    'suggested_template': suggest_template(df.columns.tolist())
                }
                
                with st.expander(f"📈 Preview: {file_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
                    with col2:
                        st.write(f"**File Size:** {data_file.size} bytes")
                    with col3:
                        suggested = st.session_state.data_files[file_name]['suggested_template']
                        st.write(f"**Suggested Template:** {suggested}")
                    
                    st.write("**Sample Columns:**")
                    cols_per_row = 4
                    for i in range(0, min(len(df.columns), 12), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col_name in enumerate(df.columns[i:i+cols_per_row]):
                            with cols[j]:
                                st.write(f"• {col_name}")
                    if len(df.columns) > 12:
                        st.write(f"... and {len(df.columns) - 12} more columns")
                    
                    st.write("**Sample Data:**")
                    st.dataframe(df.head(3), use_container_width=True)
            
            except Exception as e:
                st.error(f"Error reading data file {file_name}: {e}")

def process_dataframe_directly(mapper, df: pd.DataFrame, file_name: str, 
                              template_name: str, output_format: str, add_timestamp: bool) -> pd.DataFrame:
    """Process a DataFrame directly without saving/loading temporary files."""
    
    # Get template configuration
    template_config = mapper.config_manager.get_template_config(template_name)
    if not template_config:
        raise ValueError(f"Template '{template_name}' not found in configuration")
    
    # Get target schema
    target_columns = mapper._load_target_schema(template_config)
    
    # Find column mappings - check for manual overrides first
    if (st.session_state.current_mappings and 
        'manual_overrides' in st.session_state.current_mappings and
        st.session_state.current_mappings.get('data_file') == file_name):
        
        # Use manual mappings
        manual_overrides = st.session_state.current_mappings['manual_overrides']
        column_mappings = {k: v for k, v in manual_overrides.items() if v and v != "None"}
        st.info(f"🔧 Using manual mappings for {file_name} ({len(column_mappings)} mappings)")
    else:
        # Use automatic mappings
        column_mappings = mapper._find_column_mappings(df.columns.tolist(), template_name)
    
    # Transform data
    result_df = mapper._transform_data(df, column_mappings, target_columns, template_config)
    
    # Generate output filename and save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if add_timestamp else ""
    output_name = f"processed_{file_name.rsplit('.', 1)[0]}_{timestamp}.{output_format}"
    output_path = f"output/{output_name}"
    
    # Save output
    mapper._save_output(result_df, output_path, template_config)
    
    return result_df

def suggest_template(columns: List[str]) -> str:
    """Suggest appropriate template based on column names."""
    columns_lower = [col.lower() for col in columns]
    
    # Template 2 indicators
    template2_indicators = ['change', 'ind', 'effective date', 'relationship', 'group no']
    template2_score = sum(1 for indicator in template2_indicators 
                          if any(indicator in col for col in columns_lower))
    
    # Template 1 indicators  
    template1_indicators = ['payroll number', 'scheme number', 'child', 'spouse', 'dependant']
    template1_score = sum(1 for indicator in template1_indicators 
                          if any(indicator in col for col in columns_lower))
    
    if template2_score > template1_score:
        return "template_2"
    else:
        return "template_1"

def visualize_column_mappings():
    """Visualize column mappings between data files and templates."""
    st.markdown('<div class="section-header">🔄 Column Mapping Analysis</div>', unsafe_allow_html=True)
    
    if not st.session_state.data_files:
        st.info("Upload data files first to see mapping analysis.")
        return
    
    # Select data file for mapping analysis
    selected_data_file = st.selectbox(
        "Select data file to analyze:",
        list(st.session_state.data_files.keys())
    )
    
    if selected_data_file:
        data_info = st.session_state.data_files[selected_data_file]
        suggested_template = data_info['suggested_template']
        
        # Template selection
        template_configs = load_existing_templates()
        selected_template = st.selectbox(
            "Select target template:",
            list(template_configs.keys()),
            index=list(template_configs.keys()).index(suggested_template) if suggested_template in template_configs else 0
        )
        
        if st.button("🔍 Analyze Mapping", type="primary"):
            try:
                with st.spinner("Analyzing column mappings..."):
                    # Initialize mapper
                    if not st.session_state.mapper:
                        st.session_state.mapper = ConfigurableDataIngestionMapper(
                            config_dir="config",
                            template_name=selected_template
                        )
                    
                    # Get column mappings
                    data_columns = data_info['columns']
                    mappings = st.session_state.mapper._find_column_mappings(data_columns, selected_template)
                    
                    # Load target schema
                    template_config = template_configs[selected_template]
                    target_columns = st.session_state.mapper._load_target_schema(template_config)
                    
                    # Store mappings
                    st.session_state.current_mappings = {
                        'data_file': selected_data_file,
                        'template': selected_template,
                        'mappings': mappings,
                        'data_columns': data_columns,
                        'target_columns': target_columns
                    }
                    
                    # Display data preview to help with mapping
                    display_data_preview(data_info['dataframe'], data_columns, target_columns)
                    
                    # Display mapping results
                    display_mapping_results(mappings, data_columns, target_columns)
                    
            except Exception as e:
                st.error(f"Error analyzing mappings: {e}")
                st.code(traceback.format_exc())

def display_data_preview(df: pd.DataFrame, data_columns: List[str], target_columns: List[str]):
    """Display data preview to help with manual mapping decisions."""
    
    st.markdown("### 🔍 Data Preview")
    
    st.markdown("""
    <div class="info-box">
        <strong>Data Preview:</strong> Review sample data from your file to make informed mapping decisions.
        This helps you understand what data is in each column before mapping.
    </div>
    """, unsafe_allow_html=True)
    
    # Column selector for preview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Source Data Columns:**")
        preview_columns = st.multiselect(
            "Select columns to preview",
            data_columns,
            default=data_columns[:5] if len(data_columns) > 5 else data_columns,
            key="preview_columns"
        )
    
    with col2:
        st.markdown("**🎯 Sample Target Columns:**")
        st.multiselect(
            "Target columns (for reference)",
            target_columns,
            default=target_columns[:5] if len(target_columns) > 5 else target_columns,
            disabled=True,
            key="target_reference"
        )
    
    if preview_columns:
        st.markdown("**📋 Sample Data:**")
        preview_df = df[preview_columns].head(10)
        
        # Style the dataframe for better visibility
        styled_df = preview_df.style.set_properties(**{
            'background-color': 'rgba(46, 134, 171, 0.1)',
            'border': '1px solid rgba(46, 134, 171, 0.3)',
            'padding': '8px'
        })
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Show column statistics
        st.markdown("**📈 Column Statistics:**")
        stats_data = []
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
                "Sample Values": ", ".join([str(v)[:30] + "..." if len(str(v)) > 30 else str(v) for v in sample_values])
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)

def display_mapping_results(mappings: Dict[str, str], data_columns: List[str], target_columns: List[str]):
    """Display mapping analysis results with manual correction capabilities."""
    
    # Mapping statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Columns", len(data_columns))
    with col2:
        st.metric("Target Columns", len(target_columns))
    with col3:
        st.metric("Mapped Columns", len(mappings))
    with col4:
        coverage = (len(mappings) / len(target_columns) * 100) if target_columns else 0
        st.metric("Coverage", f"{coverage:.1f}%")
    
    # Manual mapping interface
    st.markdown("### 🔧 Manual Column Mapping")
    
    st.markdown("""
    <div class="info-box">
        <strong>Review and Correct Mappings:</strong> Below you can review automatic mappings and manually map unmapped columns.
        Use the dropdowns to correct incorrect mappings or assign source columns to unmapped targets.
    </div>
    """, unsafe_allow_html=True)
    
    # Create manual mapping interface
    manual_mappings = create_manual_mapping_interface(mappings, data_columns, target_columns)
    
    # Save manual mappings button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Manual Mappings", type="primary"):
            st.session_state.current_mappings['manual_overrides'] = manual_mappings
            st.success("✅ Manual mappings saved!")
    
    with col2:
        if st.button("🔄 Reset to Auto"):
            st.session_state.current_mappings.pop('manual_overrides', None)
            st.info("🔄 Reset to automatic mappings")
            st.rerun()
    
    with col3:
        # Show updated statistics
        if manual_mappings:
            total_mapped = len([m for m in manual_mappings.values() if m and m != "None"])
            updated_coverage = (total_mapped / len(target_columns) * 100) if target_columns else 0
            
            if updated_coverage > coverage:
                st.success(f"📈 Coverage improved to {updated_coverage:.1f}%!")
            else:
                st.info(f"📊 Current coverage: {updated_coverage:.1f}%")
    
    # Mapping visualization
    if mappings or manual_mappings:
        st.markdown("### 📊 Mapping Visualization")
        
        # Use manual mappings if available, otherwise automatic
        final_mappings = manual_mappings if manual_mappings else mappings
        
        # Create mapping dataframe
        mapping_data = []
        for target in target_columns:
            source = final_mappings.get(target, "Not Mapped")
            status = "Manual" if (manual_mappings and target in manual_mappings and manual_mappings[target]) else \
                    "Automatic" if (target in mappings) else "Unmapped"
            
            # Skip empty mappings
            if source and source != "None":
                mapping_data.append({
                    "Target Column": target,
                    "Source Column": source,
                    "Status": status
                })
            else:
                mapping_data.append({
                    "Target Column": target,
                    "Source Column": "Not Mapped",
                    "Status": "Unmapped"
                })
        
        df_mappings = pd.DataFrame(mapping_data)
        
        # Display mapping table with color coding
        st.dataframe(df_mappings, use_container_width=True)
        
        # Coverage chart
        status_counts = df_mappings['Status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Column Mapping Coverage",
            color_discrete_map={
                'Automatic': '#28a745', 
                'Manual': '#007bff', 
                'Unmapped': '#dc3545'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Export/Import mappings
        st.markdown("### 💾 Save/Load Mappings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export mappings
            if manual_mappings:
                mapping_json = json.dumps(manual_mappings, indent=2)
                st.download_button(
                    label="📥 Export Mappings",
                    data=mapping_json,
                    file_name=f"mappings_{st.session_state.current_mappings.get('data_file', 'unknown')}.json",
                    mime="application/json"
                )
        
        with col2:
            # Import mappings
            uploaded_mapping = st.file_uploader(
                "📤 Import Mappings",
                type=['json'],
                help="Upload a previously exported mapping JSON file"
            )
            
            if uploaded_mapping:
                try:
                    imported_mappings = json.loads(uploaded_mapping.read())
                    if st.button("🔄 Apply Imported Mappings"):
                        st.session_state.current_mappings['manual_overrides'] = imported_mappings
                        st.success("✅ Imported mappings applied!")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file")

def create_manual_mapping_interface(automatic_mappings: Dict[str, str], 
                                   data_columns: List[str], 
                                   target_columns: List[str]) -> Dict[str, str]:
    """Create interface for manual column mapping."""
    
    manual_mappings = {}
    
    # Add "None" option for unmapping
    source_options = ["None"] + data_columns
    
    # Create tabs for different mapping categories
    tab1, tab2, tab3 = st.tabs(["🔍 Review Auto-Mapped", "❌ Fix Unmapped", "📝 All Columns"])
    
    with tab1:
        st.markdown("**Review and Correct Automatic Mappings:**")
        
        if automatic_mappings:
            for target_col, source_col in automatic_mappings.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{target_col}**")
                
                with col2:
                    # Find current index
                    current_idx = source_options.index(source_col) if source_col in source_options else 0
                    
                    selected = st.selectbox(
                        f"Source for {target_col}",
                        source_options,
                        index=current_idx,
                        key=f"auto_{target_col}",
                        label_visibility="collapsed"
                    )
                    
                    manual_mappings[target_col] = selected if selected != "None" else ""
                
                with col3:
                    if source_col != selected:
                        st.markdown("🔄 *Modified*")
                    else:
                        st.markdown("✅ *Auto*")
        else:
            st.info("No automatic mappings found to review.")
    
    with tab2:
        st.markdown("**Map Previously Unmapped Columns:**")
        
        unmapped_targets = [col for col in target_columns if col not in automatic_mappings]
        
        if unmapped_targets:
            for target_col in unmapped_targets:
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{target_col}**")
                
                with col2:
                    selected = st.selectbox(
                        f"Source for {target_col}",
                        source_options,
                        index=0,
                        key=f"unmapped_{target_col}",
                        label_visibility="collapsed"
                    )
                    
                    manual_mappings[target_col] = selected if selected != "None" else ""
                
                with col3:
                    if selected != "None":
                        st.markdown("✅ *Mapped*")
                    else:
                        st.markdown("❌ *Unmapped*")
        else:
            st.success("🎉 All target columns are already mapped!")
    
    with tab3:
        st.markdown("**Complete Mapping Overview:**")
        
        # Show all target columns with their current mappings
        for i, target_col in enumerate(target_columns):
            with st.expander(f"📋 {target_col}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Current Mapping:**")
                    current_source = automatic_mappings.get(target_col, "Not Mapped")
                    st.write(f"→ {current_source}")
                
                with col2:
                    st.write("**Manual Override:**")
                    current_idx = source_options.index(current_source) if current_source in source_options else 0
                    
                    selected = st.selectbox(
                        "Select source column",
                        source_options,
                        index=current_idx,
                        key=f"all_{target_col}",
                        label_visibility="collapsed"
                    )
                    
                    manual_mappings[target_col] = selected if selected != "None" else ""
    
    return manual_mappings

def process_files():
    """Process uploaded files using the mapper."""
    st.markdown('<div class="section-header">⚙️ Process Files</div>', unsafe_allow_html=True)
    
    if not st.session_state.data_files:
        st.info("Upload data files first to process them.")
        return
    
    # File selection for processing
    selected_files = st.multiselect(
        "Select files to process:",
        list(st.session_state.data_files.keys()),
        default=list(st.session_state.data_files.keys())
    )
    
    # Template assignment
    template_configs = load_existing_templates()
    template_assignment = {}
    
    for file_name in selected_files:
        suggested = st.session_state.data_files[file_name]['suggested_template']
        template_assignment[file_name] = st.selectbox(
            f"Template for {file_name}:",
            list(template_configs.keys()),
            index=list(template_configs.keys()).index(suggested) if suggested in template_configs else 0,
            key=f"template_{file_name}"
        )
    
    # Processing options
    st.markdown("### ⚙️ Processing Options")
    col1, col2 = st.columns(2)
    
    with col1:
        output_format = st.selectbox("Output Format", ["xlsx", "csv"])
        include_reports = st.checkbox("Generate Processing Reports", value=True)
    
    with col2:
        preserve_names = st.checkbox("Preserve Original Names", value=False)
        add_timestamp = st.checkbox("Add Processing Timestamp", value=True)
    
    # Process button
    if st.button("🚀 Process Files", type="primary"):
        if not selected_files:
            st.warning("Please select files to process.")
            return
        
        process_selected_files(
            selected_files, 
            template_assignment, 
            output_format,
            include_reports,
            preserve_names,
            add_timestamp
        )

def process_selected_files(selected_files: List[str], template_assignment: Dict[str, str], 
                          output_format: str, include_reports: bool, preserve_names: bool, add_timestamp: bool):
    """Process the selected files."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    processed_results = []
    
    for i, file_name in enumerate(selected_files):
        try:
            status_text.text(f"Processing {file_name}...")
            progress_bar.progress((i + 1) / len(selected_files))
            
            # Get file data
            file_info = st.session_state.data_files[file_name]
            df = file_info['dataframe']
            template_name = template_assignment[file_name]
            
            # Initialize mapper
            mapper = ConfigurableDataIngestionMapper(
                config_dir="config",
                template_name=template_name
            )
            
            # Process DataFrame directly instead of saving/loading files
            result_df = process_dataframe_directly(
                mapper, df, file_name, template_name, output_format, add_timestamp
            )
            
            # Generate output filename for display
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if add_timestamp else ""
            output_name = f"processed_{file_name.rsplit('.', 1)[0]}_{timestamp}.{output_format}"
            
            # Store results
            processed_results.append({
                'original_file': file_name,
                'output_file': output_name,
                'template': template_name,
                'input_rows': len(df),
                'output_rows': len(result_df),
                'input_columns': len(df.columns),
                'output_columns': len(result_df.columns),
                'status': 'Success',
                'dataframe': result_df
            })
            
        except Exception as e:
            error_msg = str(e)
            # Make error messages more user-friendly
            if 'No engine for filetype' in error_msg or 'xlrd' in error_msg:
                error_msg = "Missing Excel library for .xls files. Please install xlrd."
            elif 'openpyxl' in error_msg:
                error_msg = "Missing Excel library for .xlsx files. Please install openpyxl."
            elif 'Permission denied' in error_msg:
                error_msg = "File is in use or permission denied. Please close the file and try again."
            elif 'No such file' in error_msg:
                error_msg = "File not found. Please check the file path."
            
            processed_results.append({
                'original_file': file_name,
                'output_file': 'Failed',
                'template': template_assignment.get(file_name, 'Unknown'),
                'status': f'Error: {error_msg}',
                'error_details': traceback.format_exc()
            })
    
    # Update session state
    st.session_state.processed_files = processed_results
    
    # Display results
    display_processing_results(results_container, processed_results)

def display_processing_results(container, results: List[Dict[str, Any]]):
    """Display processing results."""
    with container:
        st.markdown("### 📊 Processing Results")
        
        # Summary statistics
        total_files = len(results)
        successful = len([r for r in results if r['status'] == 'Success'])
        failed = total_files - successful
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", total_files)
        with col2:
            st.metric("Successful", successful, delta=successful-failed if failed > 0 else None)
        with col3:
            st.metric("Failed", failed, delta=-failed if failed > 0 else None)
        
        # Results table
        results_data = []
        for result in results:
            results_data.append({
                "File": result['original_file'],
                "Template": result['template'],
                "Status": result['status'],
                "Input Rows": result.get('input_rows', 'N/A'),
                "Output Rows": result.get('output_rows', 'N/A'),
                "Input Cols": result.get('input_columns', 'N/A'),
                "Output Cols": result.get('output_columns', 'N/A'),
                "Output File": result.get('output_file', 'N/A')
            })
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True)
        
        # Show successful processing details
        successful_results = [r for r in results if r['status'] == 'Success']
        if successful_results:
            st.markdown("### ✅ Successfully Processed Files")
            
            for result in successful_results:
                with st.expander(f"📄 {result['original_file']} → {result['output_file']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Template Used:** {result['template']}")
                        st.write(f"**Input Shape:** {result['input_rows']} × {result['input_columns']}")
                    with col2:
                        st.write(f"**Output Shape:** {result['output_rows']} × {result['output_columns']}")
                        efficiency = (result['output_columns'] / result['input_columns'] * 100) if result['input_columns'] > 0 else 0
                        st.write(f"**Column Efficiency:** {efficiency:.1f}%")
                    
                    if 'dataframe' in result:
                        st.write("**Sample Output Data:**")
                        st.dataframe(result['dataframe'].head(5), use_container_width=True)
        
        # Show error details for failed files
        failed_results = [r for r in results if r['status'] != 'Success']
        if failed_results:
            st.markdown("### ❌ Failed Processing")
            
            for result in failed_results:
                with st.expander(f"❌ {result['original_file']} - {result['status']}"):
                    if 'error_details' in result:
                        st.code(result['error_details'])

def download_processed_files():
    """Provide download options for processed files."""
    st.markdown('<div class="section-header">💾 Download Results</div>', unsafe_allow_html=True)
    
    if not st.session_state.processed_files:
        st.info("No processed files available for download.")
        return
    
    successful_results = [r for r in st.session_state.processed_files if r['status'] == 'Success']
    
    if not successful_results:
        st.warning("No successfully processed files available for download.")
        return
    
    # Individual file downloads
    st.markdown("### 📁 Individual File Downloads")
    
    for result in successful_results:
        if 'dataframe' in result:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{result['output_file']}** - {result['output_rows']} rows × {result['output_columns']} columns")
            
            with col2:
                # Convert to CSV for download
                csv_data = result['dataframe'].to_csv(index=False)
                st.download_button(
                    label="📥 CSV",
                    data=csv_data,
                    file_name=result['output_file'].replace('.xlsx', '.csv'),
                    mime="text/csv",
                    key=f"download_{result['original_file']}"
                )

def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🗂️ Configuration-Driven Data Ingestion Mapper</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3 style="margin-top: 0; color: #2E86AB;">🎉 Welcome to the Data Ingestion Mapper!</h3>
        <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
            <strong>Transform your data with confidence!</strong> This application helps you map data files to standardized templates with intelligent column matching and automated processing.
        </p>
        <hr style="border: none; border-top: 1px solid rgba(46, 134, 171, 0.3); margin: 1rem 0;">
        <p style="margin-bottom: 0;">
            <strong>Getting Started:</strong><br>
            📁 Upload your template files and data files<br>
            🔄 Visualize column mappings and coverage<br>
            ⚙️ Process files with real-time progress tracking<br>
            💾 Download standardized results
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.radio(
        "Choose a section:",
        ["🏠 Overview", "📋 Templates", "📁 Upload Files", "🔄 Mapping Analysis", "⚙️ Process Files", "💾 Download Results"]
    )
    
    # Main content based on selection
    if page == "🏠 Overview":
        st.markdown("## 🏠 Overview")
        
        # Load and display template information
        template_configs = load_existing_templates()
        display_template_info(template_configs)
        
        # System status
        st.markdown("### 🔧 System Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Available Templates", len(template_configs))
        with col2:
            st.metric("Uploaded Data Files", len(st.session_state.data_files))
        with col3:
            st.metric("Processed Files", len([r for r in st.session_state.processed_files if r['status'] == 'Success']))
    
    elif page == "📋 Templates":
        st.markdown("## 📋 Template Management")
        
        # Display existing templates
        template_configs = load_existing_templates()
        display_template_info(template_configs)
        
        # Template file upload
        st.markdown("---")
        upload_template_files()
    
    elif page == "📁 Upload Files":
        st.markdown("## 📁 File Upload")
        
        # Data file upload
        upload_data_files()
    
    elif page == "🔄 Mapping Analysis":
        st.markdown("## 🔄 Mapping Analysis")
        
        # Column mapping visualization
        visualize_column_mappings()
    
    elif page == "⚙️ Process Files":
        st.markdown("## ⚙️ File Processing")
        
        # Process files
        process_files()
    
    elif page == "💾 Download Results":
        st.markdown("## 💾 Download Results")
        
        # Download processed files
        download_processed_files()

if __name__ == "__main__":
    main()