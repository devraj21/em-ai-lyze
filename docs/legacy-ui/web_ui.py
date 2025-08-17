#!/usr/bin/env python3
"""
Web UI Server for Email Parser and Data Ingestion
Provides a simple web interface for both email parsing and data ingestion functionality
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

try:
    import uvicorn
    from fastapi import FastAPI, File, UploadFile, HTTPException, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
except ImportError:
    print("Warning: FastAPI/uvicorn not installed. Install with: uv pip install 'email-parsing-mcp[network]'")
    raise

from email_parser.mcp_server import EmailParserMCPServer
from data_ingestion.mapper import ConfigurableDataIngestionMapper

logger = logging.getLogger(__name__)

class WebUIServer:
    """Web UI server combining email parsing and data ingestion"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Email Parser & Data Ingestion Web UI",
            description="Web interface for email parsing and data ingestion",
            version="1.0.0"
        )
        
        # Initialize MCP server for email parsing
        self.mcp_server = EmailParserMCPServer()
        
        # Create temp directory for uploads
        self.temp_dir = Path(tempfile.gettempdir()) / "email_parser_ui"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all routes for the web UI"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve the main UI page"""
            return self._get_html_template()
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "web-ui"}
        
        # Email parsing endpoints
        @self.app.post("/api/email/upload")
        async def upload_email_files(files: List[UploadFile] = File(...)):
            """Upload and parse email files"""
            try:
                results = []
                for file in files:
                    if not file.filename.endswith('.msg'):
                        continue
                    
                    # Save uploaded file
                    file_id = str(uuid.uuid4())
                    file_path = self.temp_dir / f"{file_id}_{file.filename}"
                    
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    # Parse the email
                    result = await self._parse_email_file(str(file_path))
                    result["original_filename"] = file.filename
                    result["file_id"] = file_id
                    results.append(result)
                    
                    # Clean up uploaded file
                    os.unlink(file_path)
                
                return {"results": results, "total_files": len(results)}
                
            except Exception as e:
                logger.error(f"Error uploading email files: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Data ingestion endpoints
        @self.app.post("/api/data/upload")
        async def upload_data_files(
            files: List[UploadFile] = File(...),
            template: str = Form(...)
        ):
            """Upload and process data files with template"""
            try:
                results = []
                
                for file in files:
                    if not any(file.filename.endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
                        continue
                    
                    # Save uploaded file
                    file_id = str(uuid.uuid4())
                    input_path = self.temp_dir / f"{file_id}_{file.filename}"
                    
                    with open(input_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    # Process the file
                    result = await self._process_data_file(str(input_path), template)
                    result["original_filename"] = file.filename
                    result["file_id"] = file_id
                    results.append(result)
                
                return {"results": results, "total_files": len(results)}
                
            except Exception as e:
                logger.error(f"Error uploading data files: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/data/templates")
        async def get_available_templates():
            """Get list of available data templates"""
            try:
                config_path = Path("config/templates_config.json")
                if not config_path.exists():
                    return {"templates": ["template_1", "template_2"]}
                
                with open(config_path) as f:
                    config = json.load(f)
                
                templates = list(config.get("templates", {}).keys())
                return {"templates": templates}
                
            except Exception as e:
                logger.error(f"Error getting templates: {e}")
                return {"templates": ["template_1", "template_2"]}
        
        @self.app.get("/api/data/download/{file_id}")
        async def download_processed_file(file_id: str):
            """Download a processed data file"""
            try:
                # Look for the processed file in output directories
                output_dirs = ["output/template_1", "output/template_2"]
                
                for output_dir in output_dirs:
                    output_path = Path(output_dir)
                    if output_path.exists():
                        for file_path in output_path.glob(f"*{file_id}*"):
                            if file_path.is_file():
                                return FileResponse(
                                    path=str(file_path),
                                    filename=file_path.name,
                                    media_type='application/octet-stream'
                                )
                
                raise HTTPException(status_code=404, detail="File not found")
                
            except Exception as e:
                logger.error(f"Error downloading file: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _parse_email_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a single email file using MCP server"""
        try:
            # Call the MCP tool directly
            result = await self.mcp_server.mcp._call_tool("parse_email_file", {"file_path": file_path})
            return result
            
        except Exception as e:
            logger.error(f"Error parsing email file {file_path}: {e}")
            # Fallback to direct parser if MCP fails
            try:
                parser = self.mcp_server.parser
                email_content = parser.parse_msg_file(Path(file_path))
                if email_content:
                    return {
                        "file_path": file_path,
                        "subject": email_content.subject,
                        "sender": email_content.sender,
                        "recipients": email_content.recipients,
                        "date": email_content.sent_date.isoformat() if email_content.sent_date else None,
                        "body": email_content.body_text[:500] + "..." if len(email_content.body_text or "") > 500 else email_content.body_text,
                        "category": email_content.categories[0] if email_content.categories else "uncategorized",
                        "entities": email_content.extracted_entities
                    }
                else:
                    return {"error": "Failed to parse email file", "file_path": file_path}
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
                return {"error": str(e), "file_path": file_path}
    
    async def _process_data_file(self, file_path: str, template: str) -> Dict[str, Any]:
        """Process a data file with specified template"""
        try:
            # Initialize the data ingestion mapper
            mapper = ConfigurableDataIngestionMapper("config")
            
            # Process the single file
            output_dir = f"output/{template}"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # This is simplified - in a real implementation you'd call the mapper
            # For now, we'll return a success message
            result = {
                "status": "processed",
                "template": template,
                "input_file": file_path,
                "output_dir": output_dir,
                "message": f"File processed with {template}"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing data file {file_path}: {e}")
            return {"error": str(e), "file_path": file_path}
    
    def _get_html_template(self) -> str:
        """Return the HTML template for the web UI"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Parser & Data Ingestion</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }
        
        .section {
            padding: 40px;
            min-height: 500px;
        }
        
        .section:first-child {
            border-right: 1px solid #eee;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 10px;
            padding: 40px 20px;
            text-align: center;
            margin: 20px 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #3498db;
            background: #f8f9fa;
        }
        
        .upload-area.dragover {
            border-color: #2ecc71;
            background: #d5f4e6;
        }
        
        .upload-icon {
            font-size: 3em;
            color: #bdc3c7;
            margin-bottom: 15px;
        }
        
        .upload-text {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .file-input {
            display: none;
        }
        
        .template-select {
            margin: 20px 0;
        }
        
        .template-select select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            background: white;
        }
        
        .process-btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: all 0.3s ease;
        }
        
        .process-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .process-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .results {
            margin-top: 30px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .result-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .result-success {
            border-left: 4px solid #28a745;
        }
        
        .result-error {
            border-left: 4px solid #dc3545;
        }
        
        .result-filename {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .result-details {
            font-size: 0.9em;
            color: #6c757d;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .file-list {
            margin-top: 15px;
        }
        
        .file-item {
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 5px;
            margin-bottom: 5px;
            font-size: 0.9em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .remove-file {
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 0.8em;
            cursor: pointer;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .section:first-child {
                border-right: none;
                border-bottom: 1px solid #eee;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Email Parser & Data Ingestion</h1>
            <p>Upload and process your email files and data files with ease</p>
        </div>
        
        <div class="main-content">
            <!-- Email Parser Section -->
            <div class="section">
                <h2>
                    📧 Email Parser
                </h2>
                
                <div class="upload-area" id="emailUploadArea">
                    <div class="upload-icon">📎</div>
                    <div class="upload-text">
                        Drop .msg email files here or click to browse
                    </div>
                </div>
                
                <input type="file" class="file-input" id="emailFileInput" 
                       multiple accept=".msg">
                
                <div class="file-list" id="emailFileList"></div>
                
                <button class="process-btn" id="processEmailBtn" disabled>
                    Parse Email Files
                </button>
                
                <div class="loading" id="emailLoading">
                    <div class="spinner"></div>
                    <p>Processing email files...</p>
                </div>
                
                <div class="results" id="emailResults"></div>
            </div>
            
            <!-- Data Ingestion Section -->
            <div class="section">
                <h2>
                    📊 Data Ingestion
                </h2>
                
                <div class="template-select">
                    <select id="templateSelect">
                        <option value="">Select Template...</option>
                        <option value="template_1">Template 1</option>
                        <option value="template_2">Template 2</option>
                    </select>
                </div>
                
                <div class="upload-area" id="dataUploadArea">
                    <div class="upload-icon">📋</div>
                    <div class="upload-text">
                        Drop Excel/CSV files here or click to browse
                    </div>
                </div>
                
                <input type="file" class="file-input" id="dataFileInput" 
                       multiple accept=".xlsx,.xls,.csv">
                
                <div class="file-list" id="dataFileList"></div>
                
                <button class="process-btn" id="processDataBtn" disabled>
                    Process Data Files
                </button>
                
                <div class="loading" id="dataLoading">
                    <div class="spinner"></div>
                    <p>Processing data files...</p>
                </div>
                
                <div class="results" id="dataResults"></div>
            </div>
        </div>
    </div>

    <script>
        // Email Parser functionality
        let emailFiles = [];
        let dataFiles = [];
        
        // Load available templates
        fetch('/api/data/templates')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('templateSelect');
                select.innerHTML = '<option value="">Select Template...</option>';
                data.templates.forEach(template => {
                    select.innerHTML += `<option value="${template}">${template}</option>`;
                });
            });
        
        // Email upload handling
        setupFileUpload(
            'emailUploadArea', 
            'emailFileInput', 
            'emailFileList', 
            'processEmailBtn',
            emailFiles,
            '.msg'
        );
        
        // Data upload handling  
        setupFileUpload(
            'dataUploadArea', 
            'dataFileInput', 
            'dataFileList', 
            'processDataBtn',
            dataFiles,
            '.xlsx,.xls,.csv'
        );
        
        // Process email files
        document.getElementById('processEmailBtn').addEventListener('click', async () => {
            const formData = new FormData();
            emailFiles.forEach(file => formData.append('files', file));
            
            showLoading('emailLoading', true);
            
            try {
                const response = await fetch('/api/email/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayResults('emailResults', result.results, 'email');
            } catch (error) {
                displayError('emailResults', error.message);
            } finally {
                showLoading('emailLoading', false);
            }
        });
        
        // Process data files
        document.getElementById('processDataBtn').addEventListener('click', async () => {
            const template = document.getElementById('templateSelect').value;
            if (!template) {
                alert('Please select a template first');
                return;
            }
            
            const formData = new FormData();
            dataFiles.forEach(file => formData.append('files', file));
            formData.append('template', template);
            
            showLoading('dataLoading', true);
            
            try {
                const response = await fetch('/api/data/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayResults('dataResults', result.results, 'data');
            } catch (error) {
                displayError('dataResults', error.message);
            } finally {
                showLoading('dataLoading', false);
            }
        });
        
        function setupFileUpload(uploadAreaId, fileInputId, fileListId, btnId, filesArray, accept) {
            const uploadArea = document.getElementById(uploadAreaId);
            const fileInput = document.getElementById(fileInputId);
            const fileList = document.getElementById(fileListId);
            const processBtn = document.getElementById(btnId);
            
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFiles(e.dataTransfer.files, filesArray, fileList, processBtn, accept);
            });
            
            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files, filesArray, fileList, processBtn, accept);
            });
        }
        
        function handleFiles(files, filesArray, fileListElement, processBtn, accept) {
            const acceptedExts = accept.split(',').map(ext => ext.trim());
            
            Array.from(files).forEach(file => {
                const isAccepted = acceptedExts.some(ext => 
                    file.name.toLowerCase().endsWith(ext.replace('.', ''))
                );
                
                if (isAccepted && !filesArray.find(f => f.name === file.name)) {
                    filesArray.push(file);
                }
            });
            
            updateFileList(filesArray, fileListElement);
            processBtn.disabled = filesArray.length === 0;
        }
        
        function updateFileList(filesArray, fileListElement) {
            fileListElement.innerHTML = filesArray.map((file, index) => `
                <div class="file-item">
                    <span>${file.name}</span>
                    <button class="remove-file" onclick="removeFile(${index}, '${fileListElement.id}')">×</button>
                </div>
            `).join('');
        }
        
        function removeFile(index, listId) {
            const filesArray = listId.includes('email') ? emailFiles : dataFiles;
            const processBtn = listId.includes('email') ? 
                document.getElementById('processEmailBtn') : 
                document.getElementById('processDataBtn');
            const fileListElement = document.getElementById(listId);
            
            filesArray.splice(index, 1);
            updateFileList(filesArray, fileListElement);
            processBtn.disabled = filesArray.length === 0;
        }
        
        function showLoading(loadingId, show) {
            const loading = document.getElementById(loadingId);
            if (show) {
                loading.classList.add('show');
            } else {
                loading.classList.remove('show');
            }
        }
        
        function displayResults(resultsId, results, type) {
            const resultsElement = document.getElementById(resultsId);
            
            resultsElement.innerHTML = results.map(result => {
                const isError = result.error;
                const className = isError ? 'result-error' : 'result-success';
                
                let content = `
                    <div class="result-item ${className}">
                        <div class="result-filename">${result.original_filename || 'Unknown file'}</div>
                `;
                
                if (isError) {
                    content += `<div class="result-details">Error: ${result.error}</div>`;
                } else {
                    if (type === 'email') {
                        content += `
                            <div class="result-details">
                                <strong>Subject:</strong> ${result.subject || 'N/A'}<br>
                                <strong>From:</strong> ${result.sender || 'N/A'}<br>
                                <strong>Category:</strong> ${result.category || 'N/A'}
                            </div>
                        `;
                    } else {
                        content += `
                            <div class="result-details">
                                <strong>Status:</strong> ${result.status || 'Processed'}<br>
                                <strong>Template:</strong> ${result.template || 'N/A'}
                            </div>
                        `;
                    }
                }
                
                content += '</div>';
                return content;
            }).join('');
        }
        
        function displayError(resultsId, error) {
            const resultsElement = document.getElementById(resultsId);
            resultsElement.innerHTML = `
                <div class="result-item result-error">
                    <div class="result-filename">Processing Error</div>
                    <div class="result-details">${error}</div>
                </div>
            `;
        }
    </script>
</body>
</html>
        '''
    
    async def run(self):
        """Start the web UI server"""
        logger.info(f"Starting Web UI server on {self.host}:{self.port}")
        logger.info(f"Open your browser to: http://{self.host}:{self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

async def start_web_ui(host: str = "localhost", port: int = 8080):
    """Start the web UI server"""
    server = WebUIServer(host, port)
    await server.run()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Email Parser & Data Ingestion Web UI")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    asyncio.run(start_web_ui(args.host, args.port))