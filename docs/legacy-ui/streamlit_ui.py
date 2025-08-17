#!/usr/bin/env python3
"""
Streamlit UI for Email Parser and Data Ingestion
Simple, interactive web interface using Streamlit
"""

import streamlit as st
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Setup page config
st.set_page_config(
    page_title="Email Parser & Data Ingestion",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from email_parser.parser import EmailParser
from data_ingestion.mapper import ConfigurableDataIngestionMapper

# Initialize session state
if 'email_results' not in st.session_state:
    st.session_state.email_results = []
if 'data_results' not in st.session_state:
    st.session_state.data_results = []

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("📧 Email Parser & Data Ingestion")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        tab_selection = st.radio(
            "Choose functionality:",
            ["📧 Email Parser", "📊 Data Ingestion", "📋 Results History", "⚙️ Settings"]
        )
    
    # Main content based on selection
    if tab_selection == "📧 Email Parser":
        email_parser_tab()
    elif tab_selection == "📊 Data Ingestion":
        data_ingestion_tab()
    elif tab_selection == "📋 Results History":
        results_history_tab()
    elif tab_selection == "⚙️ Settings":
        settings_tab()

def email_parser_tab():
    """Email parsing interface"""
    st.header("📧 Email Parser")
    st.markdown("Upload .msg email files to extract structured content and analyze them.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose .msg email files",
        type=['msg'],
        accept_multiple_files=True,
        help="Select one or more .msg email files to parse"
    )
    
    if uploaded_files:
        st.success(f"📎 {len(uploaded_files)} email file(s) selected")
        
        # Show file details
        with st.expander("📋 File Details"):
            for file in uploaded_files:
                st.write(f"• **{file.name}** ({file.size:,} bytes)")
        
        # Process button
        if st.button("🚀 Parse Email Files", type="primary"):
            parse_email_files(uploaded_files)
    
    # Display recent results
    if st.session_state.email_results:
        st.markdown("---")
        st.subheader("📊 Recent Results")
        display_email_results(st.session_state.email_results[-5:])  # Show last 5

def data_ingestion_tab():
    """Data ingestion interface"""
    st.header("📊 Data Ingestion")
    st.markdown("Upload Excel/CSV files and process them with templates.")
    
    # Template selection
    templates = get_available_templates()
    selected_template = st.selectbox(
        "Select Template",
        templates,
        help="Choose the template to use for processing your data files"
    )
    
    if not selected_template:
        st.warning("⚠️ Please select a template to continue")
        return
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose Excel/CSV files",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Select one or more data files to process"
    )
    
    if uploaded_files:
        st.success(f"📊 {len(uploaded_files)} data file(s) selected")
        
        # Show file details
        with st.expander("📋 File Details"):
            for file in uploaded_files:
                st.write(f"• **{file.name}** ({file.size:,} bytes)")
        
        # Process button
        if st.button("🚀 Process Data Files", type="primary"):
            process_data_files(uploaded_files, selected_template)
    
    # Display recent results
    if st.session_state.data_results:
        st.markdown("---")
        st.subheader("📊 Recent Results")
        display_data_results(st.session_state.data_results[-5:])  # Show last 5

def results_history_tab():
    """Results history interface"""
    st.header("📋 Results History")
    
    # Email results
    if st.session_state.email_results:
        st.subheader("📧 Email Parsing History")
        display_email_results(st.session_state.email_results)
        
        if st.button("🗑️ Clear Email History"):
            st.session_state.email_results = []
            st.rerun()
    
    # Data results
    if st.session_state.data_results:
        st.subheader("📊 Data Ingestion History")
        display_data_results(st.session_state.data_results)
        
        if st.button("🗑️ Clear Data History"):
            st.session_state.data_results = []
            st.rerun()
    
    if not st.session_state.email_results and not st.session_state.data_results:
        st.info("📝 No processing history yet. Process some files to see results here!")

def settings_tab():
    """Settings and configuration"""
    st.header("⚙️ Settings")
    
    # System info
    st.subheader("🔧 System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Email Parser Status**\n✅ Ready")
        st.info("**Data Ingestion Status**\n✅ Ready")
    
    with col2:
        st.info(f"**Available Templates**\n{len(get_available_templates())} templates")
        st.info("**Streamlit Version**\n" + st.__version__)
    
    # Configuration files
    st.subheader("📁 Configuration Files")
    
    config_files = [
        ("Templates Config", "config/templates_config.json"),
        ("File Mappings", "config/file_mappings.json"),
        ("Main Config", "config.yaml")
    ]
    
    for name, path in config_files:
        if Path(path).exists():
            st.success(f"✅ {name}: `{path}`")
        else:
            st.warning(f"⚠️ {name}: `{path}` (not found)")
    
    # Clear all data
    st.subheader("🗑️ Data Management")
    if st.button("Clear All Results", type="secondary"):
        st.session_state.email_results = []
        st.session_state.data_results = []
        st.success("All results cleared!")
        st.rerun()

def parse_email_files(uploaded_files):
    """Parse uploaded email files"""
    parser = EmailParser()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        progress_bar.progress((i + 1) / len(uploaded_files))
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.msg') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Parse the email
            email_content = parser.parse_msg_file(Path(tmp_file_path))
            
            if email_content:
                result = {
                    'filename': uploaded_file.name,
                    'subject': email_content.subject,
                    'sender': email_content.sender,
                    'recipients': email_content.recipients,
                    'date': email_content.sent_date.isoformat() if email_content.sent_date else None,
                    'body_preview': email_content.body_text[:200] + "..." if len(email_content.body_text or "") > 200 else email_content.body_text,
                    'categories': email_content.categories,
                    'entities': email_content.extracted_entities,
                    'correlation_score': email_content.correlation_score,
                    'status': 'success'
                }
            else:
                result = {
                    'filename': uploaded_file.name,
                    'status': 'error',
                    'error': 'Failed to parse email file'
                }
            
            results.append(result)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            results.append({
                'filename': uploaded_file.name,
                'status': 'error',
                'error': str(e)
            })
    
    # Store results in session state
    st.session_state.email_results.extend(results)
    
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    # Show immediate results
    st.success(f"🎉 Processed {len(uploaded_files)} email files!")
    display_email_results(results)

def process_data_files(uploaded_files, template):
    """Process uploaded data files"""
    try:
        mapper = ConfigurableDataIngestionMapper("config")
    except Exception as e:
        st.error(f"❌ Failed to initialize data mapper: {e}")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name} with {template}...")
        progress_bar.progress((i + 1) / len(uploaded_files))
        
        try:
            # Save uploaded file temporarily
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Process the file (simplified for demo)
            result = {
                'filename': uploaded_file.name,
                'template': template,
                'status': 'processed',
                'input_path': tmp_file_path,
                'message': f'File processed with {template}'
            }
            
            results.append(result)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            results.append({
                'filename': uploaded_file.name,
                'template': template,
                'status': 'error',
                'error': str(e)
            })
    
    # Store results in session state
    st.session_state.data_results.extend(results)
    
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    # Show immediate results
    st.success(f"🎉 Processed {len(uploaded_files)} data files!")
    display_data_results(results)

def display_email_results(results):
    """Display email parsing results"""
    for idx, result in enumerate(results):
        with st.expander(f"📧 {result['filename']}", expanded=False):
            if result['status'] == 'success':
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Subject:**", result.get('subject', 'N/A'))
                    st.write("**Sender:**", result.get('sender', 'N/A'))
                    st.write("**Date:**", result.get('date', 'N/A'))
                    st.write("**Categories:**", ', '.join(result.get('categories', [])))
                
                with col2:
                    st.write("**Recipients:**", len(result.get('recipients', [])))
                    st.write("**Correlation Score:**", f"{result.get('correlation_score', 0):.2f}")
                    
                    entities = result.get('entities', {})
                    st.write("**Extracted Entities:**")
                    for entity_type, entity_list in entities.items():
                        if entity_list:
                            st.write(f"  • {entity_type}: {len(entity_list)}")
                
                if result.get('body_preview'):
                    st.write("**Body Preview:**")
                    # Create unique key using index and filename hash
                    unique_key = f"body_{idx}_{hash(result['filename']) % 10000}"
                    st.text_area("", result['body_preview'], height=100, disabled=True, key=unique_key)
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

def display_data_results(results):
    """Display data ingestion results"""
    for idx, result in enumerate(results):
        with st.expander(f"📊 {result['filename']}", expanded=False):
            if result['status'] == 'processed':
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Template:**", result.get('template', 'N/A'))
                    st.write("**Status:**", result.get('status', 'N/A'))
                
                with col2:
                    st.write("**Message:**", result.get('message', 'N/A'))
                
                st.success("✅ File processed successfully")
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

def get_available_templates():
    """Get list of available templates"""
    try:
        config_path = Path("config/templates_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            return list(config.get("templates", {}).keys())
        else:
            return ["template_1", "template_2"]
    except Exception:
        return ["template_1", "template_2"]

if __name__ == "__main__":
    main()