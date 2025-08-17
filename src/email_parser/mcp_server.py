"""
MCP Server implementation for Email Parser
Provides email parsing capabilities through Model Context Protocol
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    from fastmcp import FastMCP
except ImportError:
    print("Warning: fastmcp not installed. Install with: uv pip install fastmcp")
    FastMCP = None

from .parser import EmailParser, EmailContent

logger = logging.getLogger(__name__)

class EmailParserMCPServer:
    """MCP Server for Email Parsing"""
    
    def __init__(self, name: str = "email-parser", use_ai: bool = True, ai_model: str = "gemini-1.5-flash", use_local: bool = False):
        if FastMCP is None:
            raise ImportError("fastmcp is required. Install with: uv pip install fastmcp")
        
        self.mcp = FastMCP(name)
        self.parser = EmailParser(use_ai=use_ai, ai_model=ai_model, use_local=use_local)
        self.use_ai = use_ai
        self.use_local = use_local
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
        
    def _setup_tools(self):
        """Setup MCP tools for email parsing"""
        
        @self.mcp.tool()
        def parse_email_file(file_path: str) -> Dict[str, Any]:
            """
            Parse a single .msg email file and extract structured content.
            
            Args:
                file_path: Path to the .msg email file
                
            Returns:
                Structured email data with content, entities, and analysis
            """
            try:
                path = Path(file_path)
                if not path.exists():
                    return {"error": f"File not found: {file_path}"}
                
                if not path.suffix.lower() == '.msg':
                    return {"error": f"Unsupported file type: {path.suffix}"}
                
                email_content = self.parser.parse_msg_file(path)
                if email_content is None:
                    return {"error": "Failed to parse email file"}
                
                return self._email_content_to_dict(email_content)
                
            except Exception as e:
                logger.error(f"Error parsing email file {file_path}: {e}")
                return {"error": str(e)}
        
        @self.mcp.tool()
        def parse_email_folder(folder_path: str, output_format: str = "summary") -> Dict[str, Any]:
            """
            Parse all .msg files in a folder and return structured results.
            
            Args:
                folder_path: Path to folder containing .msg files
                output_format: Output format - "summary", "detailed", or "json"
                
            Returns:
                Batch processing results with statistics and parsed emails
            """
            try:
                folder = Path(folder_path)
                if not folder.exists() or not folder.is_dir():
                    return {"error": f"Folder not found or not a directory: {folder_path}"}
                
                msg_files = list(folder.glob("*.msg"))
                if not msg_files:
                    return {"error": f"No .msg files found in {folder_path}"}
                
                results = {
                    "total_files": len(msg_files),
                    "processed": 0,
                    "failed": 0,
                    "emails": [],
                    "statistics": {
                        "categories": {},
                        "senders": {},
                        "avg_correlation": 0.0
                    }
                }
                
                total_correlation = 0.0
                
                for msg_file in msg_files:
                    try:
                        email_content = self.parser.parse_msg_file(msg_file)
                        if email_content:
                            results["processed"] += 1
                            total_correlation += email_content.correlation_score
                            
                            # Update statistics
                            for category in email_content.categories:
                                results["statistics"]["categories"][category] = \
                                    results["statistics"]["categories"].get(category, 0) + 1
                            
                            sender_domain = email_content.sender.split('@')[-1] if '@' in email_content.sender else email_content.sender
                            results["statistics"]["senders"][sender_domain] = \
                                results["statistics"]["senders"].get(sender_domain, 0) + 1
                            
                            # Format output based on requested format
                            if output_format == "detailed":
                                results["emails"].append(self._email_content_to_dict(email_content))
                            elif output_format == "summary":
                                results["emails"].append({
                                    "file": msg_file.name,
                                    "subject": email_content.subject,
                                    "sender": email_content.sender,
                                    "categories": email_content.categories,
                                    "correlation_score": email_content.correlation_score,
                                    "summary": email_content.standardized_format.get("summary", "")
                                })
                        else:
                            results["failed"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing {msg_file}: {e}")
                        results["failed"] += 1
                
                # Calculate average correlation
                if results["processed"] > 0:
                    results["statistics"]["avg_correlation"] = total_correlation / results["processed"]
                
                return results
                
            except Exception as e:
                logger.error(f"Error parsing email folder {folder_path}: {e}")
                return {"error": str(e)}
        
        @self.mcp.tool()
        def analyze_email_patterns(folder_path: str, analysis_type: str = "categories") -> Dict[str, Any]:
            """
            Analyze patterns across multiple emails in a folder.
            
            Args:
                folder_path: Path to folder containing .msg files
                analysis_type: Type of analysis - "categories", "senders", "entities", or "all"
                
            Returns:
                Pattern analysis results and insights
            """
            try:
                folder = Path(folder_path)
                if not folder.exists() or not folder.is_dir():
                    return {"error": f"Folder not found: {folder_path}"}
                
                msg_files = list(folder.glob("*.msg"))
                if not msg_files:
                    return {"error": f"No .msg files found in {folder_path}"}
                
                analysis_results = {
                    "total_emails": len(msg_files),
                    "analysis_type": analysis_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process all emails
                emails_data = []
                for msg_file in msg_files:
                    try:
                        email_content = self.parser.parse_msg_file(msg_file)
                        if email_content:
                            emails_data.append(email_content)
                    except Exception as e:
                        logger.warning(f"Skipping {msg_file}: {e}")
                
                if not emails_data:
                    return {"error": "No emails could be processed"}
                
                analysis_results["processed_emails"] = len(emails_data)
                
                # Perform requested analysis
                if analysis_type in ["categories", "all"]:
                    analysis_results["category_analysis"] = self._analyze_categories(emails_data)
                
                if analysis_type in ["senders", "all"]:
                    analysis_results["sender_analysis"] = self._analyze_senders(emails_data)
                
                if analysis_type in ["entities", "all"]:
                    analysis_results["entity_analysis"] = self._analyze_entities(emails_data)
                
                if analysis_type == "all":
                    analysis_results["correlation_analysis"] = self._analyze_correlations(emails_data)
                
                return analysis_results
                
            except Exception as e:
                logger.error(f"Error analyzing email patterns: {e}")
                return {"error": str(e)}
        
        @self.mcp.tool()
        def extract_entities_from_text(text: str) -> Dict[str, List[str]]:
            """
            Extract entities from arbitrary text using AI-powered extraction or regex patterns.
            
            Args:
                text: Text content to analyze
                
            Returns:
                Dictionary of extracted entities by type
            """
            try:
                entities = self.parser.extract_entities_from_text(text)
                # Add AI enhancement indicator if AI was used
                if self.use_ai and hasattr(self.parser, 'ai_extractor') and self.parser.ai_extractor:
                    entities['_ai_enhanced'] = ['true']
                else:
                    entities['_ai_enhanced'] = ['false']
                return entities
            except Exception as e:
                logger.error(f"Error extracting entities: {e}")
                return {"error": str(e)}
    
    def _setup_resources(self):
        """Setup MCP resources"""
        
        @self.mcp.resource("config://parser-settings")
        def get_parser_config() -> str:
            """Get current parser configuration and entity patterns."""
            config = {
                "supported_extensions": self.parser.supported_extensions,
                "entity_patterns": self.parser.entity_patterns,
                "version": "1.0.0"
            }
            return json.dumps(config, indent=2)
        
        @self.mcp.resource("schema://email-content")
        def get_email_schema() -> str:
            """Get the schema for EmailContent structure."""
            schema = {
                "EmailContent": {
                    "message_id": "str",
                    "subject": "str", 
                    "sender": "str",
                    "recipients": "List[str]",
                    "cc_recipients": "List[str]",
                    "bcc_recipients": "List[str]",
                    "sent_date": "Optional[datetime]",
                    "body_text": "str",
                    "body_html": "str",
                    "attachments": "List[Dict[str, Any]]",
                    "priority": "str",
                    "categories": "List[str]",
                    "correlation_score": "float",
                    "extracted_entities": "Dict[str, List[str]]",
                    "standardized_format": "Dict[str, Any]"
                }
            }
            return json.dumps(schema, indent=2)
    
    def _setup_prompts(self):
        """Setup MCP prompts"""
        
        @self.mcp.prompt(title="Email Analysis Report")
        def email_analysis_prompt(folder_path: str) -> str:
            """Generate a comprehensive analysis report for emails in a folder."""
            return f"""
Please analyze all email files in the folder: {folder_path}

Generate a comprehensive report that includes:

1. **Overview Statistics**
   - Total number of emails processed
   - Date range of emails
   - Top senders and recipients

2. **Content Analysis**
   - Most common email categories
   - Priority distribution
   - Average correlation scores

3. **Entity Extraction Summary**
   - Email addresses mentioned
   - Phone numbers found
   - Dates and deadlines
   - Monetary amounts
   - URLs and links

4. **Insights and Recommendations**
   - Communication patterns
   - Potential workflow improvements
   - Action items that need attention

Use the parse_email_folder and analyze_email_patterns tools to gather the necessary data.
"""
        
        @self.mcp.prompt(title="Email Compliance Check")
        def compliance_check_prompt(email_file: str) -> str:
            """Check email for compliance and security concerns."""
            return f"""
Please perform a compliance and security analysis of the email file: {email_file}

Check for:

1. **Data Privacy Concerns**
   - Personal identifiable information (PII)
   - Credit card numbers or financial data
   - Social security numbers
   - Passwords or credentials

2. **Compliance Issues**
   - Proper sender identification
   - Unsubscribe mechanisms (for marketing emails)
   - Legal disclaimers
   - Data retention considerations

3. **Security Analysis**
   - Suspicious URLs or domains
   - Potential phishing indicators
   - Attachment security concerns
   - Sender authenticity

4. **Recommendations**
   - Actions needed for compliance
   - Security improvements
   - Data handling recommendations

Use the parse_email_file tool to extract and analyze the email content.
"""
    
    def _email_content_to_dict(self, email_content: EmailContent) -> Dict[str, Any]:
        """Convert EmailContent to dictionary for JSON serialization"""
        result = {
            "message_id": email_content.message_id,
            "subject": email_content.subject,
            "sender": email_content.sender,
            "recipients": email_content.recipients,
            "cc_recipients": email_content.cc_recipients,
            "bcc_recipients": email_content.bcc_recipients,
            "sent_date": email_content.sent_date.isoformat() if email_content.sent_date else None,
            "body_text": email_content.body_text,
            "body_html": email_content.body_html,
            "attachments": email_content.attachments,
            "priority": email_content.priority,
            "categories": email_content.categories,
            "correlation_score": email_content.correlation_score,
            "extracted_entities": email_content.extracted_entities,
            "standardized_format": email_content.standardized_format,
            # AI-enhanced fields
            "sentiment": email_content.sentiment,
            "ai_summary": email_content.ai_summary,
            "ai_priority": email_content.ai_priority,
            "ai_enhanced": email_content.ai_structured_data is not None
        }
        
        # Include structured AI data if available
        if email_content.ai_structured_data:
            result["ai_structured_data"] = {
                "summary": email_content.ai_structured_data.summary,
                "key_points": email_content.ai_structured_data.key_points,
                "action_items": email_content.ai_structured_data.action_items,
                "people_mentioned": email_content.ai_structured_data.people_mentioned,
                "dates_mentioned": email_content.ai_structured_data.dates_mentioned,
                "monetary_amounts": email_content.ai_structured_data.monetary_amounts,
                "meeting_details": email_content.ai_structured_data.meeting_details,
                "contact_information": email_content.ai_structured_data.contact_information,
                "categories": email_content.ai_structured_data.categories,
                "priority_level": email_content.ai_structured_data.priority_level,
                "sentiment": email_content.ai_structured_data.sentiment,
                "entities": email_content.ai_structured_data.entities
            }
        
        return result
    
    def _analyze_categories(self, emails_data: List[EmailContent]) -> Dict[str, Any]:
        """Analyze email categories"""
        category_stats = {}
        total_correlation = 0.0
        
        for email in emails_data:
            total_correlation += email.correlation_score
            for category in email.categories:
                if category not in category_stats:
                    category_stats[category] = {"count": 0, "correlation_sum": 0.0}
                category_stats[category]["count"] += 1
                category_stats[category]["correlation_sum"] += email.correlation_score
        
        # Calculate averages
        for category, stats in category_stats.items():
            stats["avg_correlation"] = stats["correlation_sum"] / stats["count"]
            stats["percentage"] = (stats["count"] / len(emails_data)) * 100
            del stats["correlation_sum"]  # Remove intermediate value
        
        return {
            "total_categories": len(category_stats),
            "avg_correlation_overall": total_correlation / len(emails_data),
            "categories": dict(sorted(category_stats.items(), key=lambda x: x[1]["count"], reverse=True))
        }
    
    def _analyze_senders(self, emails_data: List[EmailContent]) -> Dict[str, Any]:
        """Analyze sender patterns"""
        sender_stats = {}
        
        for email in emails_data:
            sender = email.sender
            if sender not in sender_stats:
                sender_stats[sender] = {
                    "count": 0,
                    "categories": set(),
                    "avg_correlation": 0.0,
                    "correlation_sum": 0.0
                }
            
            sender_stats[sender]["count"] += 1
            sender_stats[sender]["categories"].update(email.categories)
            sender_stats[sender]["correlation_sum"] += email.correlation_score
        
        # Calculate averages and convert sets to lists
        for sender, stats in sender_stats.items():
            stats["avg_correlation"] = stats["correlation_sum"] / stats["count"]
            stats["categories"] = list(stats["categories"])
            del stats["correlation_sum"]
        
        return {
            "total_senders": len(sender_stats),
            "senders": dict(sorted(sender_stats.items(), key=lambda x: x[1]["count"], reverse=True))
        }
    
    def _analyze_entities(self, emails_data: List[EmailContent]) -> Dict[str, Any]:
        """Analyze extracted entities"""
        entity_stats = {}
        
        for email in emails_data:
            for entity_type, entities in email.extracted_entities.items():
                if entity_type not in entity_stats:
                    entity_stats[entity_type] = {"unique_count": 0, "total_mentions": 0, "values": set()}
                
                entity_stats[entity_type]["total_mentions"] += len(entities)
                entity_stats[entity_type]["values"].update(entities)
        
        # Convert sets to lists and calculate unique counts
        for entity_type, stats in entity_stats.items():
            stats["unique_count"] = len(stats["values"])
            stats["values"] = list(stats["values"])[:20]  # Limit to first 20 for display
        
        return entity_stats
    
    def _analyze_correlations(self, emails_data: List[EmailContent]) -> Dict[str, Any]:
        """Analyze correlation patterns"""
        correlations = [email.correlation_score for email in emails_data]
        
        return {
            "avg_correlation": sum(correlations) / len(correlations),
            "min_correlation": min(correlations),
            "max_correlation": max(correlations),
            "high_correlation_count": len([c for c in correlations if c > 0.7]),
            "low_correlation_count": len([c for c in correlations if c < 0.3])
        }
    
    async def run(self, transport: str = "stdio"):
        """Run the MCP server"""
        logger.info(f"Starting Email Parser MCP Server with {transport} transport")
        
        if transport == "stdio":
            await self.mcp.run()
        else:
            raise NotImplementedError(f"Transport {transport} not yet implemented")

# Convenience function to start the server
def start_server(name: str = "email-parser", transport: str = "stdio"):
    """Start the Email Parser MCP Server"""
    server = EmailParserMCPServer(name)
    
    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use asyncio.run()
        logger.error("Already running asyncio in this thread")
        return server.run(transport)
    except RuntimeError:
        # No running loop, we can start one
        return asyncio.run(server.run(transport))

if __name__ == "__main__":
    asyncio.run(start_server())