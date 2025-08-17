# Output Directory Structure

This directory contains organized output from the Email Parser CLI and MCP server.

## 📁 Folder Structure

```
output/
├── emails/          # Single email parsing results
├── analysis/        # Pattern analysis reports
├── entities/        # Entity extraction results
├── reports/         # Comprehensive reports and summaries
└── README.md        # This file
```

## 📋 File Naming Convention

Files are automatically named with timestamps for easy organization:

- **Single emails**: `email_YYYYMMDD_HHMMSS.json`
- **Folder analysis**: `folder_analysis_YYYYMMDD_HHMMSS.json`
- **Pattern analysis**: `patterns_TYPE_YYYYMMDD_HHMMSS.json`
- **Entity extraction**: `entities_YYYYMMDD_HHMMSS.json`
- **Custom reports**: `report_NAME_YYYYMMDD_HHMMSS.json`

## 🔄 Automatic Cleanup

- Files older than 30 days are automatically archived
- Large files (>10MB) are compressed
- Duplicate analyses are merged when possible

## 🎯 Usage Examples

```bash
# Files are automatically saved to appropriate folders
python email_cli.py parse-file email.msg --format json
# → output/emails/email_20241230_143022.json

python email_cli.py analyze-patterns ./emails --type all
# → output/analysis/patterns_all_20241230_143055.json

python email_cli.py extract-entities --text "sample text"
# → output/entities/entities_20241230_143112.json
```

## 📊 Integration

The output folder is designed for:
- **Version control**: Add `output/` to `.gitignore` for local results
- **Automation**: Scripts can easily find latest results by timestamp
- **Archiving**: Structured organization for long-term storage
- **Reporting**: Dashboard tools can monitor this directory