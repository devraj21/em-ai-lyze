# 🎈 Streamlit UI Guide

## Overview

The Streamlit UI provides an alternative, data-focused interface for your email parsing and data ingestion capabilities. It's designed for interactive exploration and analysis with a clean, modern interface.

## 🚀 Quick Start

### Launch the Streamlit UI

```bash
# Method 1: Using the launcher script
python streamlit_ui.py

# Method 2: Direct Streamlit command
source .venv/bin/activate
streamlit run src/streamlit_ui.py
```

The app will automatically open in your browser at: **http://localhost:8501**

## 🎯 Features

### 📧 **Email Parser Tab**
- **Multi-file Upload**: Drag & drop or browse for .msg files
- **Real-time Processing**: Progress bars and status updates
- **Rich Results Display**: Expandable cards with detailed email information
- **Entity Analysis**: View extracted emails, phones, dates, URLs
- **Correlation Scores**: See content correlation analysis
- **Body Previews**: Quick text previews of email content

### 📊 **Data Ingestion Tab**
- **Template Selection**: Dropdown to choose processing templates
- **File Support**: Excel (.xlsx, .xls) and CSV file uploads
- **Batch Processing**: Handle multiple files simultaneously
- **Processing Status**: Real-time feedback on file processing
- **Template Integration**: Uses your existing configuration system

### 📋 **Results History Tab**
- **Persistent History**: View all previous processing results
- **Separate Sections**: Email and data ingestion histories
- **Clear Options**: Remove individual or all results
- **Detailed Views**: Expandable result cards with full information

### ⚙️ **Settings Tab**
- **System Status**: Check component health and versions
- **Configuration Info**: View available templates and config files
- **Data Management**: Clear all stored results
- **System Information**: Streamlit version and component status

## 🎨 UI Features

### **Interactive Elements**
- **Sidebar Navigation**: Easy switching between functionalities
- **Expandable Cards**: Detailed result views without clutter
- **Progress Indicators**: Real-time processing feedback
- **Status Messages**: Clear success/error messaging
- **File Previews**: Show file names and sizes before processing

### **Data Visualization**
- **Results Tables**: Organized display of processing results
- **Status Indicators**: Visual success/error states
- **Entity Summaries**: Count and type of extracted entities
- **Template Information**: Clear template usage tracking

## 🔧 Technical Details

### **Architecture**
- **Frontend**: Pure Streamlit with reactive components
- **Backend Integration**: Direct integration with your existing parsers
- **Session Management**: Persistent results across page refreshes
- **File Handling**: Secure temporary file processing
- **Error Handling**: Comprehensive error catching and display

### **Performance**
- **Async Processing**: Non-blocking file uploads
- **Memory Efficient**: Temporary file cleanup
- **Session State**: Efficient result storage
- **Progress Tracking**: Real-time processing updates

## 💡 Usage Tips

### **Email Processing**
1. Upload multiple .msg files at once for batch processing
2. Use the expandable cards to explore detailed results
3. Check the correlation scores for content analysis quality
4. Review extracted entities for data extraction accuracy

### **Data Ingestion**
1. Always select a template before uploading files
2. Use the file details expander to verify uploads
3. Monitor processing status for large files
4. Check results history for processed file tracking

### **Navigation**
- Use the sidebar to switch between different functionalities
- Results are preserved when switching tabs
- Settings tab provides system status and management options
- History tab shows all previous processing results

## 🆚 Streamlit vs FastAPI UI

| Feature | Streamlit UI | FastAPI UI |
|---------|-------------|------------|
| **Interface** | Data-focused, interactive | Web-focused, modern |
| **File Upload** | Native Streamlit widgets | Drag & drop zones |
| **Results Display** | Expandable cards, tables | JSON/card format |
| **History** | Persistent session storage | Per-session only |
| **Navigation** | Sidebar-based | Tab-based layout |
| **Best For** | Data analysis, exploration | Production web apps |

## 🔧 Customization

### **Adding New Features**
- Edit `src/streamlit_ui.py` to add new functionality
- Use Streamlit's widget library for interactive elements
- Leverage session state for persistent data storage

### **Styling**
- Streamlit uses its own theming system
- Customize with `st.set_page_config()` options
- Add custom CSS with `st.markdown()` and unsafe HTML

## 🐛 Troubleshooting

### **Common Issues**

1. **Import Errors**: Ensure you're in the project root directory
2. **Port Issues**: Streamlit uses port 8501 by default
3. **File Upload Issues**: Check file formats (.msg, .xlsx, .xls, .csv)
4. **Template Errors**: Verify `config/templates_config.json` exists

### **Performance Tips**

1. **Large Files**: Process files in smaller batches
2. **Memory Usage**: Clear results history regularly
3. **Browser Issues**: Refresh page if UI becomes unresponsive
4. **Session State**: Use browser refresh to reset session if needed

## 🎉 Getting Started

1. **Start the app**: `python streamlit_ui.py`
2. **Choose a tab**: Use sidebar navigation
3. **Upload files**: Drag & drop or browse
4. **Review results**: Expand cards for details
5. **Check history**: View all previous results

The Streamlit UI provides a perfect complement to your FastAPI web interface, offering a more data-scientist-friendly approach to email parsing and data ingestion!