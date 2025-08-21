#!/usr/bin/env python3
"""
Enhanced Streamlit UI for Em-AI-lyze Email Parser
Interactive web interface with AI, RAG, and JSON export capabilities
"""

import streamlit as st
import tempfile
import json
import os
import zipfile
import io
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

# Setup page config
st.set_page_config(
    page_title="Em-AI-lyze: AI Email Parser",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from email_parser.parser import EmailParser
    from email_parser.rag_cli import RAGKnowledgeManager, RAG_CLI_AVAILABLE
    EMAIL_PARSER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Email parser not available: {e}")
    EMAIL_PARSER_AVAILABLE = False

# Initialize session state
if 'email_results' not in st.session_state:
    st.session_state.email_results = []
if 'rag_manager' not in st.session_state:
    st.session_state.rag_manager = None
if 'ai_settings' not in st.session_state:
    st.session_state.ai_settings = {
        'use_ai': True,
        'use_local': True,
        'ai_model': 'auto',
        'use_rag': False,
        'knowledge_base_path': './email_knowledge_base'
    }
if 'widget_counter' not in st.session_state:
    st.session_state.widget_counter = 0

def get_unique_key(prefix="widget"):
    """Generate unique key for Streamlit widgets"""
    st.session_state.widget_counter += 1
    return f"{prefix}_{st.session_state.widget_counter}_{hash(str(datetime.now()))%10000}"

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🤖 Em-AI-lyze: AI Email Parser")
    st.markdown("*Advanced email analysis with AI enhancement and knowledge learning*")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        tab_selection = st.radio(
            "Choose functionality:",
            ["📧 Email Parser", "🧠 RAG Knowledge Base", "📊 Batch Processing", "📋 Results & Export", "⚙️ AI Settings"]
        )
        
        # AI Status in sidebar
        st.markdown("---")
        st.subheader("🤖 AI Status")
        display_ai_status()
    
    # Main content based on selection
    if tab_selection == "📧 Email Parser":
        email_parser_tab()
    elif tab_selection == "🧠 RAG Knowledge Base":
        rag_knowledge_tab()
    elif tab_selection == "📊 Batch Processing":
        batch_processing_tab()
    elif tab_selection == "📋 Results & Export":
        results_export_tab()
    elif tab_selection == "⚙️ AI Settings":
        ai_settings_tab()

def display_ai_status():
    """Display AI system status in sidebar"""
    if not EMAIL_PARSER_AVAILABLE:
        st.error("❌ Parser unavailable")
        return
    
    # Test parser initialization
    try:
        test_parser = EmailParser(
            use_ai=st.session_state.ai_settings['use_ai'],
            use_local=st.session_state.ai_settings['use_local'],
            ai_model=st.session_state.ai_settings['ai_model']
        )
        
        if st.session_state.ai_settings['use_ai']:
            model_type = "🏠 Local" if st.session_state.ai_settings['use_local'] else "☁️ Cloud"
            if hasattr(test_parser, 'ai_extractor') and test_parser.ai_extractor:
                st.success(f"{model_type} AI Ready")
                st.info(f"Model: {test_parser.ai_extractor.model_id}")
            else:
                st.warning("AI configured but not ready")
        else:
            st.info("🔧 Regex Mode")
        
        # RAG Status
        if RAG_CLI_AVAILABLE and st.session_state.ai_settings['use_rag']:
            try:
                if st.session_state.rag_manager is None:
                    st.session_state.rag_manager = RAGKnowledgeManager(
                        st.session_state.ai_settings['knowledge_base_path']
                    )
                stats = st.session_state.rag_manager.get_statistics()
                st.success(f"🧠 RAG Active")
                st.info(f"Emails: {stats.get('total_emails', 0)}")
            except Exception as e:
                st.warning(f"RAG setup issue: {str(e)[:30]}...")
        else:
            st.info("🧠 RAG Disabled")
            
    except Exception as e:
        st.error(f"❌ Setup error: {str(e)[:30]}...")

def email_parser_tab():
    """Enhanced email parsing interface"""
    st.header("📧 AI Email Parser")
    st.markdown("Upload .msg email files for AI-powered analysis and entity extraction.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose .msg email files",
        type=['msg'],
        accept_multiple_files=True,
        help="Select one or more .msg email files to parse with AI enhancement"
    )
    
    if uploaded_files:
        st.success(f"📎 {len(uploaded_files)} email file(s) selected")
        
        # Processing options
        col1, col2, col3 = st.columns(3)
        with col1:
            output_format = st.selectbox(
                "Output Format",
                ["Summary", "Detailed", "JSON"],
                help="Choose how to display the results"
            )
        with col2:
            add_to_rag = st.checkbox(
                "Add to Knowledge Base",
                value=st.session_state.ai_settings['use_rag'],
                help="Store parsed emails in RAG knowledge base for future context"
            )
        with col3:
            export_json = st.checkbox(
                "Export JSON",
                value=True,
                help="Generate downloadable JSON export of results"
            )
        
        # Show file details
        with st.expander("📋 File Details"):
            for file in uploaded_files:
                st.write(f"• **{file.name}** ({file.size:,} bytes)")
        
        # Process button
        if st.button("🚀 Parse Email Files", type="primary"):
            parse_email_files(uploaded_files, output_format.lower(), add_to_rag, export_json)
    
    # Display recent results
    if st.session_state.email_results:
        st.markdown("---")
        st.subheader("📊 Recent Results")
        display_email_results(st.session_state.email_results[-3:])  # Show last 3

def rag_knowledge_tab():
    """RAG knowledge base management interface"""
    st.header("🧠 RAG Knowledge Base")
    
    if not RAG_CLI_AVAILABLE:
        st.error("❌ RAG components not available. Install with: `uv pip install \".[rag]\"`")
        return
    
    # Initialize RAG manager if needed
    if st.session_state.rag_manager is None:
        try:
            st.session_state.rag_manager = RAGKnowledgeManager(
                st.session_state.ai_settings['knowledge_base_path']
            )
        except Exception as e:
            st.error(f"Failed to initialize RAG manager: {e}")
            return
    
    # Knowledge base statistics
    st.subheader("📊 Knowledge Base Statistics")
    try:
        stats = st.session_state.rag_manager.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Emails", stats.get('total_emails', 0))
        with col2:
            st.metric("Categories", stats.get('total_categories', 0))
        with col3:
            st.metric("Vector DB", "✅" if stats.get('vector_db_available') else "❌")
        with col4:
            st.metric("Embedding Model", stats.get('embedding_model', 'N/A')[:15] + "...")
        
        # Top categories
        if stats.get('top_categories'):
            st.subheader("🏷️ Top Categories")
            categories_df = pd.DataFrame(
                list(stats['top_categories'].items())[:10],
                columns=['Category', 'Count']
            )
            st.bar_chart(categories_df.set_index('Category'))
            
    except Exception as e:
        st.error(f"Error getting statistics: {e}")
    
    # Knowledge base search
    st.subheader("🔍 Search Knowledge Base")
    search_query = st.text_input("Enter search query:", placeholder="budget meeting")
    max_results = st.slider("Max results", 1, 20, 5)
    
    if st.button("🔍 Search") and search_query:
        try:
            search_results = st.session_state.rag_manager.search_knowledge_base(
                search_query, max_results
            )
            
            if 'error' in search_results:
                st.error(f"Search error: {search_results['error']}")
            else:
                st.success(f"Found {len(search_results['similar_emails'])} similar emails")
                st.write(f"**Context Summary:** {search_results.get('context_summary', 'N/A')}")
                st.write(f"**Confidence:** {search_results.get('confidence', 0):.2f}")
                
                for email in search_results['similar_emails']:
                    with st.expander(f"📧 {email['subject']}"):
                        st.write(f"**Summary:** {email['summary']}")
                        st.write(f"**Categories:** {', '.join(email['categories'])}")
                        st.write(f"**Date:** {email['timestamp']}")
                        
        except Exception as e:
            st.error(f"Search failed: {e}")
    
    # Import emails to knowledge base
    st.subheader("📥 Import Emails to Knowledge Base")
    import_files = st.file_uploader(
        "Choose .msg files to add to knowledge base",
        type=['msg'],
        accept_multiple_files=True,
        key=get_unique_key("rag_import")
    )
    
    if import_files and st.button("📥 Import to Knowledge Base"):
        import_to_rag(import_files)

def batch_processing_tab():
    """Batch processing interface"""
    st.header("📊 Batch Processing")
    st.markdown("Process multiple email files with advanced options and bulk export.")
    
    # Folder upload simulation (Streamlit limitation workaround)
    st.info("💡 **Tip:** Select multiple .msg files from the same folder for batch processing")
    
    batch_files = st.file_uploader(
        "Choose multiple .msg email files for batch processing",
        type=['msg'],
        accept_multiple_files=True,
        key=get_unique_key("batch_processing")
    )
    
    if batch_files:
        st.success(f"📦 {len(batch_files)} files ready for batch processing")
        
        # Batch options
        col1, col2 = st.columns(2)
        with col1:
            batch_add_rag = st.checkbox("Add all to Knowledge Base", value=False)
            generate_summary = st.checkbox("Generate Batch Summary", value=True)
        with col2:
            export_formats = st.multiselect(
                "Export Formats",
                ["JSON", "CSV", "Excel"],
                default=["JSON"]
            )
        
        if st.button("🚀 Process Batch", type="primary"):
            process_batch_files(batch_files, batch_add_rag, generate_summary, export_formats)

def results_export_tab():
    """Results viewing and export interface"""
    st.header("📋 Results & Export")
    
    if not st.session_state.email_results:
        st.info("📝 No processing results yet. Process some emails to see results here!")
        return
    
    # Results summary
    total_results = len(st.session_state.email_results)
    successful = len([r for r in st.session_state.email_results if r.get('status') == 'success'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Processed", total_results)
    with col2:
        st.metric("Successful", successful)
    with col3:
        st.metric("Success Rate", f"{(successful/total_results*100):.1f}%")
    
    # Export options
    st.subheader("📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export JSON", type="secondary"):
            json_data = json.dumps(st.session_state.email_results, indent=2, default=str)
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"email_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV", type="secondary"):
            df = create_results_dataframe(st.session_state.email_results)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"email_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📋 Export All", type="secondary"):
            create_bulk_export()
    
    # Results display
    st.subheader("📧 All Results")
    for idx, result in enumerate(reversed(st.session_state.email_results)):
        display_single_result(result, len(st.session_state.email_results) - idx)
    
    # Clear results
    if st.button("🗑️ Clear All Results", type="secondary"):
        st.session_state.email_results = []
        st.rerun()

def ai_settings_tab():
    """AI configuration interface"""
    st.header("⚙️ AI Settings")
    
    # AI Configuration
    st.subheader("🤖 AI Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        use_ai = st.checkbox(
            "Enable AI Processing",
            value=st.session_state.ai_settings['use_ai'],
            help="Use AI for enhanced entity extraction and analysis"
        )
        
        if use_ai:
            use_local = st.radio(
                "AI Model Type",
                ["🏠 Local (Ollama)", "☁️ Cloud (API)"],
                index=0 if st.session_state.ai_settings['use_local'] else 1,
                help="Local models provide privacy, cloud models offer higher accuracy"
            )
            use_local = use_local.startswith("🏠")
            
            ai_model = st.text_input(
                "AI Model",
                value=st.session_state.ai_settings['ai_model'],
                help="Model identifier (auto-detects best available)"
            )
    
    with col2:
        use_rag = st.checkbox(
            "Enable RAG Knowledge Base",
            value=st.session_state.ai_settings['use_rag'],
            help="Use contextual learning from historical emails"
        )
        
        if use_rag:
            knowledge_base_path = st.text_input(
                "Knowledge Base Path",
                value=st.session_state.ai_settings['knowledge_base_path'],
                help="Directory to store the email knowledge base"
            )
    
    # Save settings
    if st.button("💾 Save AI Settings", type="primary"):
        st.session_state.ai_settings.update({
            'use_ai': use_ai,
            'use_local': use_local if use_ai else True,
            'ai_model': ai_model if use_ai else 'auto',
            'use_rag': use_rag,
            'knowledge_base_path': knowledge_base_path if use_rag else './email_knowledge_base'
        })
        
        # Reset RAG manager if settings changed
        if use_rag:
            st.session_state.rag_manager = None
        
        st.success("✅ Settings saved!")
        st.rerun()
    
    # System Information
    st.subheader("🔧 System Information")
    
    # Test AI setup
    if st.button("🧪 Test AI Setup"):
        test_ai_setup()
    
    # Show current configuration
    with st.expander("📋 Current Configuration"):
        st.json(st.session_state.ai_settings)

def parse_email_files(uploaded_files, output_format, add_to_rag, export_json):
    """Parse uploaded email files with AI enhancement"""
    if not EMAIL_PARSER_AVAILABLE:
        st.error("❌ Email parser not available")
        return
    
    # Initialize parser with current settings
    parser = EmailParser(
        use_ai=st.session_state.ai_settings['use_ai'],
        use_local=st.session_state.ai_settings['use_local'],
        ai_model=st.session_state.ai_settings['ai_model'],
        use_rag=st.session_state.ai_settings['use_rag'] and add_to_rag,
        knowledge_base_path=st.session_state.ai_settings['knowledge_base_path']
    )
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"🤖 Processing {uploaded_file.name} with AI...")
        progress_bar.progress((i + 1) / len(uploaded_files))
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.msg') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Parse the email with AI
            email_content = parser.parse_msg_file(Path(tmp_file_path))
            
            if email_content:
                result = {
                    'filename': uploaded_file.name,
                    'timestamp': datetime.now().isoformat(),
                    'subject': email_content.subject,
                    'sender': email_content.sender,
                    'recipients': email_content.recipients,
                    'cc_recipients': email_content.cc_recipients,
                    'sent_date': email_content.sent_date.isoformat() if email_content.sent_date else None,
                    'ai_summary': getattr(email_content, 'ai_summary', ''),
                    'sentiment': getattr(email_content, 'sentiment', 'neutral'),
                    'ai_priority': getattr(email_content, 'ai_priority', 'medium'),
                    'body_preview': email_content.body_text[:300] + "..." if len(email_content.body_text or "") > 300 else email_content.body_text,
                    'categories': email_content.categories,
                    'extracted_entities': email_content.extracted_entities,
                    'correlation_score': email_content.correlation_score,
                    'standardized_format': email_content.standardized_format,
                    'knowledge_confidence': getattr(email_content, 'knowledge_confidence', 0),
                    'context_summary': getattr(email_content, 'context_summary', ''),
                    'attachments_count': len(email_content.attachments),
                    'status': 'success',
                    'ai_enhanced': st.session_state.ai_settings['use_ai']
                }
            else:
                result = {
                    'filename': uploaded_file.name,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': 'Failed to parse email file'
                }
            
            results.append(result)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            results.append({
                'filename': uploaded_file.name,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            })
    
    # Store results in session state
    st.session_state.email_results.extend(results)
    
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    # Show immediate results
    successful = len([r for r in results if r['status'] == 'success'])
    st.success(f"🎉 Processed {successful}/{len(uploaded_files)} email files successfully!")
    
    # Display results based on format
    if output_format == "summary":
        display_email_results(results)
    elif output_format == "detailed":
        display_detailed_results(results)
    elif output_format == "json":
        st.json(results)
    
    # Export JSON if requested
    if export_json and results:
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="💾 Download JSON Results",
            data=json_data,
            file_name=f"email_parse_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def import_to_rag(import_files):
    """Import files to RAG knowledge base"""
    if not st.session_state.rag_manager:
        st.error("❌ RAG manager not initialized")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Save files temporarily
    temp_folder = tempfile.mkdtemp()
    
    try:
        for i, uploaded_file in enumerate(import_files):
            status_text.text(f"📥 Importing {uploaded_file.name}...")
            progress_bar.progress((i + 1) / len(import_files))
            
            # Save to temp folder
            temp_path = Path(temp_folder) / uploaded_file.name
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
        
        # Import to RAG
        results = st.session_state.rag_manager.import_emails_from_folder(temp_folder)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Import complete!")
        
        if 'error' in results:
            st.error(f"Import failed: {results['error']}")
        else:
            st.success(f"📥 Imported {results['processed']}/{results['total_files']} emails to knowledge base")
            if results['errors']:
                with st.expander("⚠️ Import Errors"):
                    for error in results['errors']:
                        st.write(f"• {error}")
    
    finally:
        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_folder, ignore_errors=True)

def process_batch_files(batch_files, add_to_rag, generate_summary, export_formats):
    """Process multiple files in batch mode"""
    st.info(f"🚀 Starting batch processing of {len(batch_files)} files...")
    
    # Process files
    parse_email_files(batch_files, "summary", add_to_rag, False)
    
    # Generate batch summary
    if generate_summary:
        st.subheader("📊 Batch Processing Summary")
        generate_batch_summary()
    
    # Generate exports
    if export_formats:
        st.subheader("📤 Batch Exports")
        for fmt in export_formats:
            if fmt == "JSON":
                json_data = json.dumps(st.session_state.email_results, indent=2, default=str)
                st.download_button(
                    label=f"💾 Download {fmt}",
                    data=json_data,
                    file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key=get_unique_key(f"batch_{fmt}")
                )
            elif fmt == "CSV":
                df = create_results_dataframe(st.session_state.email_results)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label=f"💾 Download {fmt}",
                    data=csv_data,
                    file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=get_unique_key(f"batch_{fmt}")
                )

def display_email_results(results):
    """Display email parsing results in summary format"""
    for idx, result in enumerate(results):
        with st.expander(f"📧 {result['filename']}", expanded=False):
            if result['status'] == 'success':
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Subject:**", result.get('subject', 'N/A'))
                    st.write("**Sender:**", result.get('sender', 'N/A'))
                    st.write("**Date:**", result.get('sent_date', 'N/A'))
                    st.write("**Categories:**", ', '.join(result.get('categories', [])))
                    if result.get('ai_enhanced'):
                        st.write("**AI Summary:**", result.get('ai_summary', 'N/A'))
                
                with col2:
                    st.write("**Recipients:**", len(result.get('recipients', [])))
                    st.write("**Correlation Score:**", f"{result.get('correlation_score', 0):.2f}")
                    if result.get('ai_enhanced'):
                        st.write("**Sentiment:**", result.get('sentiment', 'N/A'))
                        st.write("**Priority:**", result.get('ai_priority', 'N/A'))
                        if result.get('knowledge_confidence', 0) > 0:
                            st.write("**Knowledge Confidence:**", f"{result.get('knowledge_confidence', 0):.2f}")
                    
                    entities = result.get('extracted_entities', {})
                    entity_count = sum(len(v) for v in entities.values() if isinstance(v, list))
                    st.write("**Extracted Entities:**", entity_count)
                
                if result.get('body_preview'):
                    st.write("**Body Preview:**")
                    st.text_area("", result['body_preview'], height=80, disabled=True, key=get_unique_key("body_preview"))
            
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

def display_detailed_results(results):
    """Display detailed email parsing results"""
    for result in results:
        if result['status'] == 'success':
            st.subheader(f"📧 {result['filename']}")
            
            # Basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Subject:**", result.get('subject', 'N/A'))
                st.write("**Sender:**", result.get('sender', 'N/A'))
                st.write("**Date:**", result.get('sent_date', 'N/A'))
            with col2:
                st.write("**Recipients:**", len(result.get('recipients', [])))
                st.write("**CC Recipients:**", len(result.get('cc_recipients', [])))
                st.write("**Attachments:**", result.get('attachments_count', 0))
            with col3:
                st.write("**Correlation Score:**", f"{result.get('correlation_score', 0):.2f}")
                if result.get('ai_enhanced'):
                    st.write("**Sentiment:**", result.get('sentiment', 'N/A'))
                    st.write("**Priority:**", result.get('ai_priority', 'N/A'))
            
            # AI Analysis
            if result.get('ai_enhanced'):
                st.write("**AI Summary:**", result.get('ai_summary', 'N/A'))
                if result.get('context_summary'):
                    st.write("**Context Summary:**", result.get('context_summary', 'N/A'))
            
            # Categories and Entities
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Categories:**")
                for cat in result.get('categories', []):
                    st.write(f"• {cat}")
            
            with col2:
                st.write("**Extracted Entities:**")
                entities = result.get('extracted_entities', {})
                for entity_type, entity_list in entities.items():
                    if entity_list and not entity_type.startswith('_'):
                        st.write(f"• **{entity_type}:** {', '.join(entity_list[:3])}")
            
            # Standardized format
            if result.get('standardized_format'):
                with st.expander("📋 Standardized Format"):
                    st.json(result['standardized_format'])
            
            st.markdown("---")

def display_single_result(result, number):
    """Display a single result with numbering"""
    with st.expander(f"{number}. 📧 {result['filename']} ({result.get('timestamp', '')[:16]})", expanded=False):
        if result['status'] == 'success':
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Subject:**", result.get('subject', 'N/A'))
                st.write("**Sender:**", result.get('sender', 'N/A'))
                if result.get('ai_enhanced'):
                    st.write("**AI Summary:**", result.get('ai_summary', 'N/A')[:100] + "...")
            
            with col2:
                st.write("**Categories:**", ', '.join(result.get('categories', [])))
                if result.get('ai_enhanced'):
                    st.write("**Sentiment:**", result.get('sentiment', 'N/A'))
                    st.write("**Priority:**", result.get('ai_priority', 'N/A'))
        else:
            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

def create_results_dataframe(results):
    """Create pandas DataFrame from results for export"""
    data = []
    for result in results:
        if result['status'] == 'success':
            data.append({
                'filename': result.get('filename', ''),
                'timestamp': result.get('timestamp', ''),
                'subject': result.get('subject', ''),
                'sender': result.get('sender', ''),
                'recipients_count': len(result.get('recipients', [])),
                'sent_date': result.get('sent_date', ''),
                'ai_summary': result.get('ai_summary', ''),
                'sentiment': result.get('sentiment', ''),
                'priority': result.get('ai_priority', ''),
                'categories': ', '.join(result.get('categories', [])),
                'correlation_score': result.get('correlation_score', 0),
                'entities_count': sum(len(v) for v in result.get('extracted_entities', {}).values() if isinstance(v, list)),
                'ai_enhanced': result.get('ai_enhanced', False),
                'knowledge_confidence': result.get('knowledge_confidence', 0)
            })
    
    return pd.DataFrame(data)

def create_bulk_export():
    """Create a bulk export with multiple formats"""
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # JSON export
        json_data = json.dumps(st.session_state.email_results, indent=2, default=str)
        zip_file.writestr("email_results.json", json_data)
        
        # CSV export
        df = create_results_dataframe(st.session_state.email_results)
        csv_data = df.to_csv(index=False)
        zip_file.writestr("email_results.csv", csv_data)
        
        # Summary report
        summary = generate_summary_report()
        zip_file.writestr("summary_report.txt", summary)
    
    zip_buffer.seek(0)
    
    st.download_button(
        label="📦 Download All Formats (ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"email_analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip"
    )

def generate_batch_summary():
    """Generate batch processing summary"""
    if not st.session_state.email_results:
        return
    
    total = len(st.session_state.email_results)
    successful = len([r for r in st.session_state.email_results if r.get('status') == 'success'])
    ai_enhanced = len([r for r in st.session_state.email_results if r.get('ai_enhanced')])
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files", total)
    with col2:
        st.metric("Successful", successful)
    with col3:
        st.metric("AI Enhanced", ai_enhanced)
    with col4:
        st.metric("Success Rate", f"{(successful/total*100):.1f}%")
    
    # Category analysis
    all_categories = []
    sentiments = []
    priorities = []
    
    for result in st.session_state.email_results:
        if result.get('status') == 'success':
            all_categories.extend(result.get('categories', []))
            if result.get('sentiment'):
                sentiments.append(result['sentiment'])
            if result.get('ai_priority'):
                priorities.append(result['ai_priority'])
    
    if all_categories:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Categories:**")
            category_counts = pd.Series(all_categories).value_counts().head(10)
            st.bar_chart(category_counts)
        
        with col2:
            if sentiments:
                st.write("**Sentiment Distribution:**")
                sentiment_counts = pd.Series(sentiments).value_counts()
                st.bar_chart(sentiment_counts)

def generate_summary_report():
    """Generate text summary report"""
    if not st.session_state.email_results:
        return "No results available"
    
    total = len(st.session_state.email_results)
    successful = len([r for r in st.session_state.email_results if r.get('status') == 'success'])
    
    report = f"""
Email Analysis Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
========
Total Files Processed: {total}
Successfully Parsed: {successful}
Success Rate: {(successful/total*100):.1f}%

AI ENHANCEMENT STATUS
===================
AI Enhanced Emails: {len([r for r in st.session_state.email_results if r.get('ai_enhanced')])}
RAG Knowledge Used: {len([r for r in st.session_state.email_results if r.get('knowledge_confidence', 0) > 0])}

DETAILED RESULTS
===============
"""
    
    for i, result in enumerate(st.session_state.email_results):
        if result.get('status') == 'success':
            report += f"""
{i+1}. {result.get('filename', 'Unknown')}
   Subject: {result.get('subject', 'N/A')}
   Sender: {result.get('sender', 'N/A')}
   Categories: {', '.join(result.get('categories', []))}
   Sentiment: {result.get('sentiment', 'N/A')}
   Priority: {result.get('ai_priority', 'N/A')}
   Correlation Score: {result.get('correlation_score', 0):.2f}
"""
    
    return report

def test_ai_setup():
    """Test AI configuration and models"""
    st.write("🧪 Testing AI Setup...")
    
    try:
        # Test basic parser
        test_parser = EmailParser(
            use_ai=st.session_state.ai_settings['use_ai'],
            use_local=st.session_state.ai_settings['use_local'],
            ai_model=st.session_state.ai_settings['ai_model']
        )
        
        st.success("✅ EmailParser initialization successful")
        
        if st.session_state.ai_settings['use_ai']:
            if hasattr(test_parser, 'ai_extractor') and test_parser.ai_extractor:
                st.success(f"✅ AI Extractor ready: {test_parser.ai_extractor.model_id}")
                
                # Test entity extraction
                test_text = "Meeting tomorrow at 2 PM with John Smith. Budget is $50,000."
                entities = test_parser.extract_entities_from_text(test_text)
                
                if entities:
                    st.success("✅ Entity extraction test passed")
                    st.write("**Test Results:**")
                    for entity_type, values in entities.items():
                        if values and not entity_type.startswith('_'):
                            st.write(f"• {entity_type}: {values}")
                else:
                    st.warning("⚠️ Entity extraction returned empty results")
            else:
                st.error("❌ AI Extractor not available")
        
        # Test RAG if enabled
        if st.session_state.ai_settings['use_rag'] and RAG_CLI_AVAILABLE:
            try:
                test_rag = RAGKnowledgeManager(st.session_state.ai_settings['knowledge_base_path'])
                stats = test_rag.get_statistics()
                st.success(f"✅ RAG system ready: {stats.get('total_emails', 0)} emails in knowledge base")
            except Exception as e:
                st.error(f"❌ RAG system error: {e}")
        
    except Exception as e:
        st.error(f"❌ AI setup test failed: {e}")

if __name__ == "__main__":
    if EMAIL_PARSER_AVAILABLE:
        main()
    else:
        st.error("❌ Email parser components not available. Please check installation.")
        st.code("uv pip install -e \".[all]\"", language="bash")