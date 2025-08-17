#!/usr/bin/env python3
"""
Enhanced CLI for Email Parser with full AI and Ollama support
"""

import argparse
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def parse_single_file(file_path: str, use_local: bool = False, ai_model: str = "gemini-1.5-flash", output_format: str = "summary") -> None:
    """Parse a single email file"""
    try:
        from email_parser.parser import EmailParser
        
        print(f"🔍 Parsing email file: {file_path}")
        
        # Initialize parser
        parser = EmailParser(use_ai=True, use_local=use_local, ai_model=ai_model)
        model_type = "local" if use_local else "cloud"
        if hasattr(parser, 'ai_extractor') and parser.ai_extractor:
            print(f"🤖 Using {model_type} AI model: {parser.ai_extractor.model_id}")
        
        # Parse the file
        email_data = parser.parse_msg_file(Path(file_path))
        
        if not email_data:
            print("❌ Failed to parse email file")
            return
        
        print("✅ Email parsed successfully!")
        
        # Output based on format
        if output_format == "summary":
            print(f"\n📧 Email Summary:")
            print(f"Subject: {email_data.subject}")
            print(f"From: {email_data.sender}")
            print(f"To: {', '.join(email_data.recipients[:3])}{'...' if len(email_data.recipients) > 3 else ''}")
            print(f"Date: {email_data.sent_date}")
            print(f"AI Summary: {email_data.ai_summary}")
            print(f"Sentiment: {email_data.sentiment}")
            print(f"Priority: {email_data.ai_priority}")
            print(f"Categories: {', '.join(email_data.categories)}")
        
        elif output_format == "detailed":
            print(f"\n📧 Detailed Email Analysis:")
            print(f"Subject: {email_data.subject}")
            print(f"From: {email_data.sender}")
            print(f"To: {', '.join(email_data.recipients)}")
            print(f"CC: {', '.join(email_data.cc_recipients)}")
            print(f"Date: {email_data.sent_date}")
            print(f"Priority: {email_data.priority} (AI: {email_data.ai_priority})")
            print(f"Categories: {', '.join(email_data.categories)}")
            print(f"Sentiment: {email_data.sentiment}")
            print(f"Correlation Score: {email_data.correlation_score:.2f}")
            
            if email_data.attachments:
                print(f"Attachments: {len(email_data.attachments)} files")
            
            print(f"\nAI Summary: {email_data.ai_summary}")
            
            if email_data.extracted_entities:
                print(f"\n🔍 Extracted Entities:")
                for entity_type, values in email_data.extracted_entities.items():
                    if values and not entity_type.startswith('_'):
                        print(f"  • {entity_type.title()}: {', '.join(values)}")
            
            if email_data.standardized_format.get('action_items'):
                print(f"\n✅ Action Items:")
                for item in email_data.standardized_format['action_items']:
                    print(f"  • {item}")
        
        elif output_format == "json":
            # Convert to JSON-serializable format
            email_dict = {
                'subject': email_data.subject,
                'sender': email_data.sender,
                'recipients': email_data.recipients,
                'sent_date': email_data.sent_date.isoformat() if email_data.sent_date else None,
                'ai_summary': email_data.ai_summary,
                'sentiment': email_data.sentiment,
                'ai_priority': email_data.ai_priority,
                'categories': email_data.categories,
                'extracted_entities': email_data.extracted_entities,
                'correlation_score': email_data.correlation_score
            }
            print(json.dumps(email_dict, indent=2))
            
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: uv pip install 'email-parsing-mcp[ai]'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing email: {e}")
        sys.exit(1)

def parse_folder(folder_path: str, use_local: bool = False, ai_model: str = "gemini-1.5-flash", output_format: str = "summary") -> None:
    """Parse all emails in a folder"""
    try:
        from email_parser.parser import EmailParser
        
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            print(f"❌ Folder not found: {folder_path}")
            sys.exit(1)
        
        # Find .msg files
        msg_files = list(folder.glob("*.msg"))
        if not msg_files:
            print(f"❌ No .msg files found in {folder_path}")
            sys.exit(1)
        
        print(f"🔍 Found {len(msg_files)} email files")
        
        # Initialize parser
        parser = EmailParser(use_ai=True, use_local=use_local, ai_model=ai_model)
        model_type = "local" if use_local else "cloud"
        if hasattr(parser, 'ai_extractor') and parser.ai_extractor:
            print(f"🤖 Using {model_type} AI model: {parser.ai_extractor.model_id}")
        
        # Parse all files
        results = []
        successful = 0
        
        for msg_file in msg_files:
            try:
                email_data = parser.parse_msg_file(msg_file)
                if email_data:
                    results.append(email_data)
                    successful += 1
                    print(f"✅ Parsed: {msg_file.name}")
                else:
                    print(f"❌ Failed: {msg_file.name}")
            except Exception as e:
                print(f"❌ Error parsing {msg_file.name}: {e}")
        
        print(f"\n📊 Results: {successful}/{len(msg_files)} emails parsed successfully")
        
        # Summary statistics
        if results:
            categories = {}
            sentiments = {}
            priorities = {}
            
            for email in results:
                for category in email.categories:
                    categories[category] = categories.get(category, 0) + 1
                sentiments[email.sentiment] = sentiments.get(email.sentiment, 0) + 1
                priorities[email.ai_priority] = priorities.get(email.ai_priority, 0) + 1
            
            print(f"\n📈 Analysis Summary:")
            print(f"Top Categories: {dict(list(sorted(categories.items(), key=lambda x: x[1], reverse=True))[:3])}")
            print(f"Sentiment Distribution: {sentiments}")
            print(f"Priority Distribution: {priorities}")
            
            if output_format == "detailed":
                print(f"\n📧 Individual Email Summaries:")
                for email in results:
                    print(f"\n• {email.subject}")
                    print(f"  From: {email.sender}")
                    print(f"  Summary: {email.ai_summary[:100]}...")
                    print(f"  Sentiment: {email.sentiment}, Priority: {email.ai_priority}")
            
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: uv pip install 'email-parsing-mcp[ai]'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing folder: {e}")
        sys.exit(1)

def extract_entities(text: str, use_local: bool = False, ai_model: str = "gemini-1.5-flash") -> None:
    """Extract entities from arbitrary text"""
    try:
        from email_parser.parser import EmailParser
        
        print(f"🔍 Extracting entities from text...")
        
        # Initialize parser
        parser = EmailParser(use_ai=True, use_local=use_local, ai_model=ai_model)
        model_type = "local" if use_local else "cloud"
        if hasattr(parser, 'ai_extractor') and parser.ai_extractor:
            print(f"🤖 Using {model_type} AI model: {parser.ai_extractor.model_id}")
        
        # Extract entities
        entities = parser.extract_entities_from_text(text)
        
        print(f"\n📝 Input Text:")
        print(f'"{text[:200]}{"..." if len(text) > 200 else ""}"')
        
        print(f"\n🔍 Extracted Entities:")
        entity_count = 0
        for entity_type, values in entities.items():
            if values and not entity_type.startswith('_'):
                print(f"  • {entity_type.title()}: {values}")
                entity_count += len(values)
        
        if entity_count == 0:
            print("  No entities found")
        
        # Show AI status
        ai_used = entities.get('_ai_enhanced', ['false'])[0] == 'true'
        print(f"\n🤖 Processing: {'AI Enhanced' if ai_used else 'Regex Fallback'}")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: uv pip install 'email-parsing-mcp[ai]'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error extracting entities: {e}")
        sys.exit(1)

def test_setup() -> None:
    """Test the installation and setup"""
    print("🧪 Testing Email Parser Setup")
    print("=" * 40)
    
    # Test basic imports
    try:
        from email_parser.parser import EmailParser
        print("✅ Core parser import successful")
    except ImportError as e:
        print(f"❌ Core parser import failed: {e}")
        return
    
    # Test AI imports
    try:
        from email_parser.ai_extractor import AIEmailExtractor
        print("✅ AI extractor import successful")
    except ImportError as e:
        print(f"❌ AI extractor import failed: {e}")
        print("Install with: uv pip install 'email-parsing-mcp[ai]'")
    
    # Test Ollama availability
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print("✅ Ollama is available")
                print(f"   Available models: {len(lines) - 1}")
                for line in lines[1:4]:  # Show first 3 models
                    model_name = line.split()[0]
                    print(f"   • {model_name}")
            else:
                print("⚠️ Ollama installed but no models found")
                print("   Try: ollama pull llama3.2:1b")
        else:
            print("❌ Ollama command failed")
    except:
        print("❌ Ollama not found")
        print("   Install from: https://ollama.ai")
    
    # Test parser initialization
    try:
        # Test with local AI
        parser_local = EmailParser(use_ai=True, use_local=True)
        print("✅ Local AI parser initialization successful")
        if hasattr(parser_local, 'ai_extractor') and parser_local.ai_extractor:
            print(f"   Using model: {parser_local.ai_extractor.model_id}")
    except Exception as e:
        print(f"⚠️ Local AI parser initialization failed: {e}")
    
    try:
        # Test without AI
        parser_basic = EmailParser(use_ai=False)
        print("✅ Basic parser initialization successful")
    except Exception as e:
        print(f"❌ Basic parser initialization failed: {e}")
    
    print("\n🎉 Setup test completed!")

def compare_processing(file_path: str) -> None:
    """Compare local vs cloud processing on the same file"""
    try:
        from email_parser.parser import EmailParser
        
        print(f"🔄 Comparing Local vs Cloud Processing")
        print(f"File: {file_path}")
        print("=" * 50)
        
        # Test with local AI
        print("\n🏠 LOCAL AI PROCESSING:")
        print("-" * 25)
        parser_local = EmailParser(use_ai=True, use_local=True)
        if hasattr(parser_local, 'ai_extractor') and parser_local.ai_extractor:
            print(f"Model: {parser_local.ai_extractor.model_id}")
        
        email_local = parser_local.parse_msg_file(Path(file_path))
        if email_local:
            print(f"✅ Success")
            print(f"Summary: {email_local.ai_summary[:100]}...")
            print(f"Sentiment: {email_local.sentiment}")
            print(f"Categories: {', '.join(email_local.categories[:3])}")
            print(f"Entities: {sum(len(v) for v in email_local.extracted_entities.values() if not str(v).startswith('_'))}")
        
        # Test with cloud AI
        print("\n☁️ CLOUD AI PROCESSING:")
        print("-" * 25)
        parser_cloud = EmailParser(use_ai=True, use_local=False)
        email_cloud = parser_cloud.parse_msg_file(Path(file_path))
        if email_cloud:
            print(f"✅ Success")
            print(f"Summary: {email_cloud.ai_summary[:100]}...")
            print(f"Sentiment: {email_cloud.sentiment}")
            print(f"Categories: {', '.join(email_cloud.categories[:3])}")
            print(f"Entities: {sum(len(v) for v in email_cloud.extracted_entities.values() if not str(v).startswith('_'))}")
        else:
            print("❌ Failed (likely no API key)")
        
        # Test regex-only
        print("\n🔧 REGEX-ONLY PROCESSING:")
        print("-" * 25)
        parser_regex = EmailParser(use_ai=False)
        email_regex = parser_regex.parse_msg_file(Path(file_path))
        if email_regex:
            print(f"✅ Success")
            print(f"Categories: {', '.join(email_regex.categories[:3])}")
            print(f"Entities: {sum(len(v) for v in email_regex.extracted_entities.values())}")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error in comparison: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Em-AI-lyze: AI-powered email analysis with local and cloud processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse single email with local AI
  python cli.py parse --file email.msg --local

  # Parse folder with cloud AI  
  python cli.py parse-folder --folder emails/ --output detailed

  # Extract entities from text with Ollama
  python cli.py extract --text "Meeting tomorrow at 2 PM" --local

  # Compare processing methods
  python cli.py compare --file email.msg

  # Test setup
  python cli.py test
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Parse single file
    parse_parser = subparsers.add_parser('parse', help='Parse a single email file')
    parse_parser.add_argument('--file', required=True, help='Path to .msg email file')
    parse_parser.add_argument('--local', action='store_true', help='Use local Ollama models')
    parse_parser.add_argument('--model', default='gemini-1.5-flash', help='AI model to use')
    parse_parser.add_argument('--output', choices=['summary', 'detailed', 'json'], default='summary', help='Output format')
    
    # Parse folder
    folder_parser = subparsers.add_parser('parse-folder', help='Parse all emails in a folder')
    folder_parser.add_argument('--folder', required=True, help='Path to folder containing .msg files')
    folder_parser.add_argument('--local', action='store_true', help='Use local Ollama models')
    folder_parser.add_argument('--model', default='gemini-1.5-flash', help='AI model to use')
    folder_parser.add_argument('--output', choices=['summary', 'detailed'], default='summary', help='Output format')
    
    # Extract entities
    extract_parser = subparsers.add_parser('extract', help='Extract entities from text')
    extract_parser.add_argument('--text', required=True, help='Text to analyze')
    extract_parser.add_argument('--local', action='store_true', help='Use local Ollama models')
    extract_parser.add_argument('--model', default='gemini-1.5-flash', help='AI model to use')
    
    # Compare processing
    compare_parser = subparsers.add_parser('compare', help='Compare local vs cloud processing')
    compare_parser.add_argument('--file', required=True, help='Path to .msg email file')
    
    # Test setup
    subparsers.add_parser('test', help='Test installation and setup')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute commands
    if args.command == 'parse':
        parse_single_file(args.file, args.local, args.model, args.output)
    elif args.command == 'parse-folder':
        parse_folder(args.folder, args.local, args.model, args.output)
    elif args.command == 'extract':
        extract_entities(args.text, args.local, args.model)
    elif args.command == 'compare':
        compare_processing(args.file)
    elif args.command == 'test':
        test_setup()

if __name__ == "__main__":
    main()