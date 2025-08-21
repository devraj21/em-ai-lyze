# Configuration-Driven Data Ingestion Mapper

A Streamlit web application for mapping data files to standardized templates with intelligent column mapping and data transformation capabilities.

## 🎯 Overview

This application provides a user-friendly interface for the configuration-driven data ingestion mapper, allowing users to:

- **Upload Template Files**: Define target schemas for data mapping
- **Upload Data Files**: Process group files, change files, or any structured data
- **Visualize Mappings**: See how columns are mapped between source and target
- **Process Files**: Transform data according to configured rules
- **Download Results**: Get processed files in standardized formats

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install required dependencies (if not already installed)
uv pip install streamlit plotly
```

### 2. Start the Application

```bash
# Easy start (recommended)
python start_data_ingestion_ui.py

# Or manually
streamlit run data_ingestion_streamlit.py
```

### 3. Access the UI

Open your browser and navigate to: **http://localhost:8503**

## 📁 File Structure

```
📦 Data Ingestion Mapper
├── 📄 data_ingestion_streamlit.py    # Main Streamlit application
├── 📄 start_data_ingestion_ui.py     # Startup script
├── 📄 test_data_ingestion_ui.py      # Test suite
├── 📂 src/data_ingestion/             # Core mapper logic
├── 📂 config/                         # Configuration files
├── 📂 template/                       # Template files
├── 📂 examples/                       # Sample data files
└── 📂 output/                         # Processed output files
```

## 🎛️ Application Features

### 📋 Template Management
- **View Available Templates**: See configured templates with descriptions
- **Upload New Templates**: Add custom template files
- **Template Preview**: Examine column structures and sample data

### 📊 File Processing
- **Multi-file Upload**: Drag and drop multiple files
- **Auto Template Detection**: Smart template suggestion based on content
- **Column Mapping Visualization**: Interactive mapping display
- **Processing Options**: Configure output format and settings

### 📈 Data Analysis
- **Mapping Coverage**: See percentage of columns successfully mapped
- **Data Quality Metrics**: Analyze completeness and patterns
- **Processing Reports**: Detailed transformation summaries

### 💾 Results Management
- **Download Processed Files**: Get results in CSV or Excel format
- **Processing Reports**: Access detailed transformation logs
- **Batch Processing**: Handle multiple files simultaneously

## 🔧 Configuration

The mapper uses JSON configuration files in the `config/` directory:

### templates_config.json
Defines available templates, column mappings, and transformation rules:

```json
{
  "templates": {
    "template_1": {
      "name": "Batchload Data Template",
      "template_file": "template/Batchload files/Batchload Data Template.xlsx",
      "data_transformations": {
        "date_format": "DD/MM/YYYY",
        "gender_standardization": {"M": "Male", "F": "Female"}
      }
    }
  }
}
```

### file_mappings.json
Maps input file patterns to appropriate templates:

```json
{
  "file_mappings": [
    {
      "name": "Batchload Files",
      "template": "template_1",
      "input_patterns": ["examples/Batchload files/*.csv"]
    }
  ]
}
```

## 📊 Supported Data Types

### Template Files (Target Schemas)
- **Excel Files**: `.xlsx`, `.xls`
- **CSV Files**: `.csv`
- **Multiple Sheets**: Configurable sheet selection

### Data Files (Sources)
- **Excel Files**: `.xlsx`, `.xls` 
- **CSV Files**: `.csv`
- **Mixed Formats**: Process different formats together

## 🔄 Mapping Algorithm

The intelligent mapping system uses:

1. **Exact Name Matching**: Direct column name matches
2. **Fuzzy Matching**: Handles variations in naming conventions
3. **Pattern-Based Mapping**: Regex patterns for family/dependent structures
4. **Configuration-Driven Rules**: Customizable mapping logic
5. **Multi-Alias Support**: Multiple source names for each target column

### Example Mappings
```
Target: "Surname" ← Sources: ["Surname", "SURNAME", "last_name"]
Target: "Date of Birth" ← Sources: ["DOB", "dob", "DateOfBirth"]
Target: "Child 1 Forename" ← Pattern: "CHILD FORENAME 1"
```

## 🎨 User Interface

### Navigation Sections
- **🏠 Overview**: System status and template information
- **📋 Templates**: Template management and upload
- **📁 Upload Files**: Data file upload and preview
- **🔄 Mapping Analysis**: Column mapping visualization
- **⚙️ Process Files**: File processing and configuration
- **💾 Download Results**: Results download and management

### Visual Features
- **Progress Bars**: Real-time processing status
- **Interactive Charts**: Mapping coverage visualization
- **Data Previews**: Sample data display
- **Color-coded Status**: Success/error indicators

## 📈 Processing Workflow

1. **Upload Templates**: Define your target data structure
2. **Upload Data Files**: Add files to be processed
3. **Review Mappings**: Verify column mapping accuracy
4. **Configure Processing**: Set output format and options
5. **Process Files**: Execute data transformation
6. **Download Results**: Get standardized output files

## 🔍 Quality Control

### Data Validation
- **Required Field Checking**: Ensure critical columns are mapped
- **Data Type Validation**: Verify compatible data types
- **Empty Data Detection**: Identify columns with no data

### Processing Reports
- **Mapping Summary**: Detailed column mapping information
- **Data Quality Metrics**: Coverage and completeness statistics
- **Error Reporting**: Clear error messages and suggestions

## 🛠️ Advanced Features

### Pattern-Based Mapping
Handles complex family/dependent structures:
```
Input: "CHILD FORENAME 1", "CHILD FORENAME 2", ...
Output: "Child 1 Forename", "Child 2 Forename", ...
```

### Data Transformations
- **Date Standardization**: Convert to consistent formats
- **Gender Mapping**: Standardize M/F to Male/Female
- **Name Case Formatting**: Title case for names
- **Postcode Formatting**: Uppercase postal codes

### Batch Processing
- Process multiple files with different templates
- Automatic template detection and assignment
- Parallel processing for improved performance

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run comprehensive tests
python test_data_ingestion_ui.py

# Test specific functionality
python -c "from src.data_ingestion.mapper import ConfigurableDataIngestionMapper; print('✅ Mapper ready')"
```

## 📋 Requirements

### Core Dependencies
- `streamlit` - Web application framework
- `plotly` - Data visualization
- `pandas` - Data manipulation
- `openpyxl` - Excel file support

### Existing Modules
- `src.data_ingestion.mapper` - Core mapping logic
- `src.data_ingestion.config_manager` - Configuration management

## 🚨 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install missing dependencies
uv pip install streamlit plotly
```

**File Upload Issues**
- Check file formats (only .xlsx, .xls, .csv supported)
- Verify file size limits
- Ensure files are not corrupted

**Mapping Problems**
- Review column names for exact matches
- Check configuration files for correct patterns
- Verify template files are accessible

## 🎯 Use Cases

### 1. HR Data Processing
- **Templates**: Employee data schemas
- **Source Files**: Various HR system exports
- **Output**: Standardized employee records

### 2. Customer Data Integration
- **Templates**: CRM data structures
- **Source Files**: Multiple customer databases
- **Output**: Unified customer profiles

### 3. Financial Data Consolidation
- **Templates**: Accounting system schemas
- **Source Files**: Branch/division reports
- **Output**: Consolidated financial data

## 🔮 Future Enhancements

- **Real-time Processing**: Live data transformation
- **Advanced Validation**: Custom validation rules
- **API Integration**: REST API for programmatic access
- **Machine Learning**: AI-powered column mapping
- **Collaborative Features**: Multi-user template management

## 📞 Support

For issues or questions:
1. Check the test suite: `python test_data_ingestion_ui.py`
2. Review configuration files in `config/`
3. Examine logs and error messages
4. Refer to existing documentation in `docs/`

---

**🎉 Happy Data Mapping!** Transform your data with confidence using the Configuration-Driven Data Ingestion Mapper.