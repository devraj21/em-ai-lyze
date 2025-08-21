#!/usr/bin/env python3
"""
Configuration-Driven Data Ingestion Mapper

Enhanced version that uses JSON configuration files to define templates,
column mappings, and file processing rules. This makes the system highly
flexible and maintainable without code changes.
"""

import pandas as pd
import os
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging
from .config_manager import ConfigurationManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigurableDataIngestionMapper:
    """
    Configuration-driven data ingestion mapper that uses JSON config files
    to define templates, column mappings, and processing rules.
    """
    
    def __init__(self, config_dir: str = "config", template_name: str = None):
        """
        Initialize the mapper with configuration files.
        
        Args:
            config_dir: Directory containing configuration files
            template_name: Optional specific template to use (overrides file-based detection)
        """
        self.config_manager = ConfigurationManager(config_dir)
        self.forced_template = template_name
        
        # Validate configuration
        errors = self.config_manager.validate_configuration()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise ValueError("Invalid configuration. Please check config files.")
        
        self.processing_rules = self.config_manager.get_processing_rules()
        logger.info("Configurable Data Ingestion Mapper initialized successfully")
    
    def process_file(self, input_file_path: str, output_file_path: str = None) -> pd.DataFrame:
        """
        Process a single input file using configuration-driven mapping.
        
        Args:
            input_file_path: Path to input file
            output_file_path: Optional path for output file
            
        Returns:
            Processed dataframe in target schema format
        """
        logger.info(f"Processing file: {input_file_path}")
        
        # Determine template to use
        template_name = self.forced_template or self.config_manager.resolve_file_template(input_file_path)
        template_config = self.config_manager.get_template_config(template_name)
        
        if not template_config:
            raise ValueError(f"Template '{template_name}' not found in configuration")
        
        logger.info(f"Using template: {template_name} - {template_config.get('name', '')}")
        
        # Read input file
        df, file_type = self._read_input_file(input_file_path, template_config)
        logger.info(f"Read {len(df)} rows from {file_type} file")
        
        # Get target schema
        target_columns = self._load_target_schema(template_config)
        logger.info(f"Target schema has {len(target_columns)} columns")
        
        # Find column mappings
        column_mappings = self._find_column_mappings(df.columns.tolist(), template_name)
        logger.info(f"Found {len(column_mappings)} column mappings")
        
        # Log mappings for review
        for target, source in column_mappings.items():
            logger.info(f"  {target} <- {source}")
        
        # Transform data
        result_df = self._transform_data(df, column_mappings, target_columns, template_config)
        
        # Generate processing report
        report_data = self._generate_processing_report(
            input_file_path, template_name, template_config, 
            df, result_df, column_mappings
        )
        
        # Save processing report
        self._save_processing_report(report_data, input_file_path, template_name)
        
        # Save output if path provided
        if output_file_path:
            self._save_output(result_df, output_file_path, template_config)
        
        return result_df
    
    def process_batch_auto(self, input_folders: List[str] = None, base_output_dir: str = "output") -> Dict[str, List[str]]:
        """
        Process files automatically based on configuration mappings.
        
        Args:
            input_folders: Optional list of input folders to scan (uses config if None)
            base_output_dir: Base output directory
            
        Returns:
            Dictionary of template -> list of processed files
        """
        results = {}
        
        if input_folders is None:
            # Get input patterns from configuration
            input_folders = self._get_configured_input_patterns()
        
        # Process each configured file mapping
        for mapping in self.config_manager.file_mappings_config.get("file_mappings", []):
            if not mapping.get("enabled", True):
                continue
            
            template_name = mapping["template"]
            if template_name not in results:
                results[template_name] = []
            
            # Find files matching patterns
            files_to_process = self._find_files_for_mapping(mapping)
            
            if files_to_process:
                logger.info(f"Processing {len(files_to_process)} files for template '{template_name}'")
                output_folder = mapping.get("output_folder", f"{base_output_dir}/{template_name}")
                
                for file_path in files_to_process:
                    try:
                        output_filename = self._generate_output_filename(file_path, template_name)
                        output_path = os.path.join(output_folder, output_filename)
                        
                        self.process_file(file_path, output_path)
                        results[template_name].append(output_path)
                        
                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {e}")
                        if not self.config_manager.file_mappings_config.get("processing_options", {}).get("continue_on_error", True):
                            raise
        
        return results
    
    def _read_input_file(self, file_path: str, template_config: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        """Read input file with template-specific configuration."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
                file_type = 'csv'
            elif file_ext in ['.xls', '.xlsx']:
                read_kwargs = {}
                
                # Use template-specific sheet name if specified
                sheet_name = template_config.get("sheet_name")
                if sheet_name:
                    read_kwargs["sheet_name"] = sheet_name
                
                # Use template-specific header row
                header_row = template_config.get("header_row", 0)
                read_kwargs["header"] = header_row
                
                # Add engine specification for better compatibility
                if file_ext == '.xls':
                    read_kwargs["engine"] = 'xlrd'
                elif file_ext == '.xlsx':
                    read_kwargs["engine"] = 'openpyxl'
                
                df = pd.read_excel(file_path, **read_kwargs)
                file_type = file_ext[1:]  # Remove the dot
                
                # Handle special case where first row contains better headers
                if template_config.get("use_first_row_as_headers", False) and len(df) > 0:
                    df = self._use_first_row_as_headers(df)
                
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
            return df, file_type
            
        except ImportError as e:
            if 'xlrd' in str(e) or 'openpyxl' in str(e):
                logger.error(f"Missing required library for reading {file_ext} files. Please install: pip install xlrd openpyxl")
                raise ImportError(f"Missing Excel library. Install with: pip install xlrd openpyxl")
            else:
                logger.error(f"Import error reading file {file_path}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def _use_first_row_as_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use first row as column headers for templates that need it."""
        if len(df) == 0:
            return df
        
        new_columns = []
        for i, col in enumerate(df.columns):
            header_val = df.iloc[0, i] if pd.notna(df.iloc[0, i]) else None
            if header_val and str(header_val) != 'nan' and not str(col).startswith('Unnamed'):
                new_columns.append(str(header_val))
            elif not str(col).startswith('Unnamed'):
                new_columns.append(str(col))
            else:
                new_columns.append(f'Column_{i+1}')
        
        df.columns = new_columns
        df = df.iloc[1:].reset_index(drop=True)  # Remove the header row from data
        return df
    
    def _load_target_schema(self, template_config: Dict[str, Any]) -> List[str]:
        """Load target schema from template file."""
        template_file = template_config.get("template_file")
        
        if not template_file or not os.path.exists(template_file):
            logger.warning(f"Template file not found: {template_file}")
            return []
        
        try:
            read_kwargs = {}
            if template_config.get("sheet_name"):
                read_kwargs["sheet_name"] = template_config["sheet_name"]
            
            df_template = pd.read_excel(template_file, **read_kwargs)
            
            # Handle special header processing if needed
            if template_config.get("use_first_row_as_headers", False):
                df_template = self._use_first_row_as_headers(df_template)
            
            return df_template.columns.tolist()
            
        except Exception as e:
            logger.error(f"Error loading target schema from {template_file}: {e}")
            return []
    
    def _find_column_mappings(self, input_columns: List[str], template_name: str) -> Dict[str, str]:
        """Find mappings between input columns and target schema using configuration."""
        mappings = {}
        
        # Get flattened column mappings from configuration
        config_mappings = self.config_manager.flatten_column_mappings(template_name)
        
        # Normalize input columns for matching
        normalized_input = {self._normalize_column_name(col): col for col in input_columns}
        
        # Match configured mappings
        for target_col, possible_names in config_mappings.items():
            if isinstance(possible_names, list):
                for possible_name in possible_names:
                    normalized_possible = self._normalize_column_name(possible_name)
                    if normalized_possible in normalized_input:
                        mappings[target_col] = normalized_input[normalized_possible]
                        break
        
        # Handle pattern-based mappings (like children/dependants)
        pattern_mappings = self._find_pattern_mappings(input_columns, template_name)
        mappings.update(pattern_mappings)
        
        return mappings
    
    def _find_pattern_mappings(self, input_columns: List[str], template_name: str) -> Dict[str, str]:
        """Find pattern-based column mappings (like children, dependants)."""
        pattern_mappings = {}
        column_mappings = self.config_manager.get_column_mappings(template_name)
        
        # Handle children patterns for standard template
        if template_name == "standard":
            children_config = column_mappings.get("children_patterns", {})
            max_children = children_config.get("max_children", 5)
            
            for field_type, patterns in children_config.items():
                if field_type == "max_children":
                    continue
                
                for input_col in input_columns:
                    normalized = self._normalize_column_name(input_col)
                    for pattern in patterns:
                        match = re.search(pattern, normalized)
                        if match:
                            child_num = int(match.group(1))
                            if child_num <= max_children:
                                if field_type == "forename":
                                    target_col = f'Child {child_num} Forename'
                                elif field_type == "surname":
                                    target_col = f'Child {child_num} Surname'
                                elif field_type == "sex":
                                    target_col = f'Child {child_num} Sex'
                                elif field_type == "dob":
                                    target_col = f'Child {child_num} Dob'
                                
                                if target_col:
                                    pattern_mappings[target_col] = input_col
        
        # Handle dependant patterns for template_2 (UK Membership template)
        elif template_name == "template_2":
            dependant_config = column_mappings.get("dependant_patterns", {})
            max_dependants = dependant_config.get("max_dependants", 10)
            
            for field_type, patterns in dependant_config.items():
                if field_type == "max_dependants":
                    continue
                
                for input_col in input_columns:
                    normalized = self._normalize_column_name(input_col)
                    for pattern in patterns:
                        match = re.search(pattern, normalized)
                        if match:
                            dep_num = int(match.group(1))
                            if dep_num <= max_dependants:
                                if field_type == "surname":
                                    target_col = f'Surname{dep_num}'
                                elif field_type == "forename":
                                    target_col = f'First Name{dep_num}'
                                elif field_type == "title":
                                    target_col = f'Title{dep_num}'
                                elif field_type == "sex":
                                    target_col = f'Sex{dep_num}'
                                elif field_type == "dob":
                                    target_col = f'Date of Birth{dep_num}'
                                elif field_type == "relationship":
                                    target_col = f'Relationship{dep_num}'
                                
                                if target_col:
                                    pattern_mappings[target_col] = input_col
        
        return pattern_mappings
    
    def _normalize_column_name(self, col_name: str) -> str:
        """Normalize column names for matching."""
        return re.sub(r'[^\w\s]', '', str(col_name).strip().lower())
    
    def _transform_data(self, df: pd.DataFrame, mappings: Dict[str, str], 
                       target_columns: List[str], template_config: Dict[str, Any]) -> pd.DataFrame:
        """Transform data according to template configuration."""
        # Create output dataframe with target schema
        output_df = pd.DataFrame(columns=target_columns)
        
        # Map and copy data
        for target_col, input_col in mappings.items():
            if input_col in df.columns and target_col in output_df.columns:
                output_df[target_col] = df[input_col]
        
        # Apply template-specific transformations
        transformations = template_config.get("data_transformations", {})
        
        # Date standardization
        date_format = transformations.get("date_format", "DD/MM/YYYY")
        date_columns = self._get_date_columns(target_columns, template_config)
        
        for col in date_columns:
            if col in output_df.columns:
                if date_format == "DD/MM/YYYY":
                    output_df[col] = pd.to_datetime(output_df[col], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
                elif date_format == "YYYY-MM-DD":
                    output_df[col] = pd.to_datetime(output_df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Gender standardization
        gender_map = transformations.get("gender_standardization", {})
        if gender_map:
            gender_columns = self._get_gender_columns(target_columns, template_config)
            for col in gender_columns:
                if col in output_df.columns:
                    output_df[col] = output_df[col].astype(str).str.upper().map(gender_map).fillna(output_df[col])
        
        # Name case formatting
        name_case = transformations.get("name_case", "title")
        if name_case == "title":
            name_columns = self._get_name_columns(target_columns, template_config)
            for col in name_columns:
                if col in output_df.columns:
                    output_df[col] = output_df[col].astype(str).str.strip().str.title()
                    output_df[col] = output_df[col].replace('Nan', '')
        
        # Postcode formatting
        postcode_case = transformations.get("postcode_case", "upper")
        postcode_columns = self._get_postcode_columns(target_columns, template_config)
        for col in postcode_columns:
            if col in output_df.columns and postcode_case == "upper":
                output_df[col] = output_df[col].astype(str).str.upper().str.strip()
        
        return output_df
    
    def _get_date_columns(self, columns: List[str], template_config: Dict[str, Any]) -> List[str]:
        """Identify date columns based on naming patterns."""
        date_patterns = ['dob', 'date of birth', 'date', 'birth']
        return [col for col in columns if any(pattern in col.lower() for pattern in date_patterns)]
    
    def _get_gender_columns(self, columns: List[str], template_config: Dict[str, Any]) -> List[str]:
        """Identify gender/sex columns."""
        gender_patterns = ['sex', 'gender']
        return [col for col in columns if any(pattern in col.lower() for pattern in gender_patterns)]
    
    def _get_name_columns(self, columns: List[str], template_config: Dict[str, Any]) -> List[str]:
        """Identify name columns."""
        name_patterns = ['name', 'surname', 'forename', 'title']
        return [col for col in columns if any(pattern in col.lower() for pattern in name_patterns)]
    
    def _get_postcode_columns(self, columns: List[str], template_config: Dict[str, Any]) -> List[str]:
        """Identify postcode columns."""
        return [col for col in columns if 'post' in col.lower() and 'code' in col.lower()]
    
    def _generate_output_filename(self, input_path: str, template_name: str) -> str:
        """Generate output filename based on input and template."""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        template_config = self.config_manager.get_template_config(template_name)
        suffix = template_config.get("output_suffix", "")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"processed_{base_name}{suffix}_{timestamp}.xlsx"
    
    def _save_output(self, df: pd.DataFrame, output_path: str, template_config: Dict[str, Any]):
        """Save processed dataframe to output file."""
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Determine output format
        output_format = self.processing_rules.get("output", {}).get("file_format", "xlsx")
        
        if output_format == "csv" or output_path.endswith('.csv'):
            df.to_csv(output_path, index=False)
        else:
            # Default to Excel
            if not output_path.endswith('.xlsx'):
                output_path = os.path.splitext(output_path)[0] + '.xlsx'
            df.to_excel(output_path, index=False)
        
        logger.info(f"Output saved to: {output_path}")
    
    def _find_files_for_mapping(self, mapping: Dict[str, Any]) -> List[str]:
        """Find files that match a mapping configuration."""
        files = []
        
        for pattern in mapping.get("input_patterns", []):
            import glob
            matched_files = glob.glob(pattern)
            for file_path in matched_files:
                # Check exclusions
                excluded = False
                for exclude_pattern in mapping.get("exclude_patterns", []):
                    if self.config_manager._match_pattern(file_path, exclude_pattern):
                        excluded = True
                        break
                
                if not excluded:
                    files.append(file_path)
        
        return files
    
    def _get_configured_input_patterns(self) -> List[str]:
        """Get all input patterns from configuration."""
        patterns = []
        for mapping in self.config_manager.file_mappings_config.get("file_mappings", []):
            if mapping.get("enabled", True):
                patterns.extend(mapping.get("input_patterns", []))
        return patterns
    
    def generate_mapping_report(self, input_folder: str = None) -> str:
        """Generate a comprehensive mapping analysis report."""
        report = []
        report.append("CONFIGURATION-DRIVEN DATA INGESTION MAPPING REPORT")
        report.append("=" * 60)
        report.append(f"Configuration Version: {self.config_manager.templates_config.get('version', 'Unknown')}")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Available templates
        templates = self.config_manager.get_available_templates()
        report.append(f"Available Templates ({len(templates)}):")
        for template in templates:
            config = self.config_manager.get_template_config(template)
            report.append(f"  - {template}: {config.get('name', 'No description')}")
        report.append("")
        
        # Process files if input folder provided
        if input_folder:
            self._add_folder_analysis_to_report(report, input_folder)
        
        return "\n".join(report)
    
    def _add_folder_analysis_to_report(self, report: List[str], input_folder: str):
        """Add file analysis to the report."""
        import glob
        
        supported_extensions = ['.csv', '.xls', '.xlsx']
        for ext in supported_extensions:
            pattern = os.path.join(input_folder, f"*{ext}")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    template_name = self.config_manager.resolve_file_template(file_path)
                    template_config = self.config_manager.get_template_config(template_name)
                    
                    df, file_type = self._read_input_file(file_path, template_config)
                    target_columns = self._load_target_schema(template_config)
                    mappings = self._find_column_mappings(df.columns.tolist(), template_name)
                    
                    report.append(f"File: {os.path.basename(file_path)} ({file_type.upper()})")
                    report.append(f"  Template: {template_name}")
                    report.append(f"  Rows: {len(df)}")
                    report.append(f"  Input Columns: {len(df.columns)}")
                    report.append(f"  Target Columns: {len(target_columns)}")
                    report.append(f"  Mapped Columns: {len(mappings)}")
                    if len(target_columns) > 0:
                        coverage = len(mappings) / len(target_columns) * 100
                        report.append(f"  Coverage: {coverage:.1f}%")
                    
                    if mappings:
                        report.append("  Key Mappings:")
                        for target, source in list(mappings.items())[:5]:
                            report.append(f"    {target} <- {source}")
                        if len(mappings) > 5:
                            report.append(f"    ... and {len(mappings) - 5} more")
                    
                    report.append("")
                    
                except Exception as e:
                    report.append(f"File: {os.path.basename(file_path)} - ERROR: {e}")
                    report.append("")

    def _generate_processing_report(self, input_file_path: str, template_name: str, 
                                   template_config: Dict[str, Any], original_df: pd.DataFrame, 
                                   processed_df: pd.DataFrame, column_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a comprehensive processing report.
        
        Args:
            input_file_path: Path to the input file
            template_name: Template used for processing
            template_config: Template configuration
            original_df: Original input dataframe
            processed_df: Processed output dataframe
            column_mappings: Column mappings applied
            
        Returns:
            Processing report data
        """
        # Analyze affected columns
        affected_columns = []
        for target_col, source_col in column_mappings.items():
            if source_col in original_df.columns:
                non_null_count = original_df[source_col].notna().sum()
                affected_columns.append({
                    "target_column": target_col,
                    "source_column": source_col,
                    "records_with_data": int(non_null_count),
                    "records_empty": int(len(original_df) - non_null_count),
                    "data_percentage": float(non_null_count / len(original_df) * 100) if len(original_df) > 0 else 0
                })
        
        # Generate report data
        report_data = {
            "processing_timestamp": datetime.now().isoformat(),
            "file_info": {
                "input_file": os.path.basename(input_file_path),
                "input_file_path": input_file_path,
                "file_size_mb": round(os.path.getsize(input_file_path) / (1024*1024), 2) if os.path.exists(input_file_path) else 0
            },
            "template_info": {
                "template_id": template_name,
                "template_name": template_config.get("name", "Unknown"),
                "template_description": template_config.get("description", ""),
                "template_file": template_config.get("template_file", "")
            },
            "processing_summary": {
                "total_input_records": len(original_df),
                "total_output_records": len(processed_df),
                "input_columns": len(original_df.columns),
                "output_columns": len(processed_df.columns),
                "mapped_columns": len(column_mappings),
                "mapping_coverage_percentage": round(len(column_mappings) / len(processed_df.columns) * 100, 2) if len(processed_df.columns) > 0 else 0
            },
            "column_mappings": [
                {
                    "target_column": target,
                    "source_column": source
                }
                for target, source in column_mappings.items()
            ],
            "affected_columns_detail": affected_columns,
            "data_quality_metrics": {
                "columns_with_data": len([col for col in affected_columns if col["records_with_data"] > 0]),
                "completely_empty_columns": len([col for col in affected_columns if col["records_with_data"] == 0]),
                "average_data_coverage": round(sum([col["data_percentage"] for col in affected_columns]) / len(affected_columns), 2) if affected_columns else 0
            }
        }
        
        return report_data
    
    def _save_processing_report(self, report_data: Dict[str, Any], input_file_path: str, template_name: str):
        """
        Save the processing report to a log file.
        
        Args:
            report_data: Report data to save
            input_file_path: Original input file path
            template_name: Template used
        """
        # Create reports directory
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = os.path.splitext(os.path.basename(input_file_path))[0]
        report_filename = f"{input_filename}_{template_name}_{timestamp}_report.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        # Save JSON report
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Processing report saved: {report_path}")
            
            # Also create a human-readable summary
            summary_path = report_path.replace('.json', '_summary.txt')
            self._save_human_readable_report(report_data, summary_path)
            
        except Exception as e:
            logger.error(f"Failed to save processing report: {e}")
    
    def _save_human_readable_report(self, report_data: Dict[str, Any], summary_path: str):
        """
        Save a human-readable processing report.
        
        Args:
            report_data: Report data
            summary_path: Path to save the summary
        """
        try:
            with open(summary_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("DATA INGESTION PROCESSING REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Processing timestamp
                f.write(f"Processing Time: {report_data['processing_timestamp']}\n\n")
                
                # File information
                file_info = report_data['file_info']
                f.write("FILE INFORMATION:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Input File: {file_info['input_file']}\n")
                f.write(f"File Path: {file_info['input_file_path']}\n")
                f.write(f"File Size: {file_info['file_size_mb']} MB\n\n")
                
                # Template information
                template_info = report_data['template_info']
                f.write("TEMPLATE INFORMATION:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Template ID: {template_info['template_id']}\n")
                f.write(f"Template Name: {template_info['template_name']}\n")
                f.write(f"Description: {template_info['template_description']}\n")
                f.write(f"Template File: {template_info['template_file']}\n\n")
                
                # Processing summary
                summary = report_data['processing_summary']
                f.write("PROCESSING SUMMARY:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Input Records: {summary['total_input_records']:,}\n")
                f.write(f"Total Output Records: {summary['total_output_records']:,}\n")
                f.write(f"Input Columns: {summary['input_columns']}\n")
                f.write(f"Output Columns: {summary['output_columns']}\n")
                f.write(f"Mapped Columns: {summary['mapped_columns']}\n")
                f.write(f"Mapping Coverage: {summary['mapping_coverage_percentage']}%\n\n")
                
                # Data quality metrics
                quality = report_data['data_quality_metrics']
                f.write("DATA QUALITY METRICS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Columns with Data: {quality['columns_with_data']}\n")
                f.write(f"Empty Columns: {quality['completely_empty_columns']}\n")
                f.write(f"Average Data Coverage: {quality['average_data_coverage']}%\n\n")
                
                # Column mappings
                f.write("COLUMN MAPPINGS:\n")
                f.write("-" * 40 + "\n")
                for mapping in report_data['column_mappings']:
                    f.write(f"{mapping['target_column']} <- {mapping['source_column']}\n")
                
                # Affected columns detail
                f.write(f"\nAFFECTED COLUMNS DETAIL:\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'Target Column':<30} {'Source Column':<30} {'Records':<10} {'Coverage':<10}\n")
                f.write("-" * 80 + "\n")
                
                for col in report_data['affected_columns_detail']:
                    f.write(f"{col['target_column']:<30} {col['source_column']:<30} "
                           f"{col['records_with_data']:<10} {col['data_percentage']:.1f}%\n")
                
                f.write("\n" + "=" * 80 + "\n")
                
            logger.info(f"Human-readable report saved: {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to save human-readable report: {e}")


if __name__ == "__main__":
    # Test the configuration-driven mapper
    try:
        mapper = ConfigurableDataIngestionMapper()
        
        # Generate report
        report = mapper.generate_mapping_report("examples/Batchload files")
        print(report)
        
        # Test single file processing
        test_file = "examples/Batchload files/Group 2.csv"
        if os.path.exists(test_file):
            print(f"\nTesting single file processing: {test_file}")
            result = mapper.process_file(test_file)
            print(f"Processed {len(result)} rows with {len(result.columns)} columns")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()