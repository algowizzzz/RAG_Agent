#!/usr/bin/env python3
"""
Generic Report Generator
=======================

A flexible script to generate AI-powered reports from JSON retrieval results
using the Refine Synthesis Tool with Gemini API.

CONFIGURATION:
- Edit the CONFIG section below to customize your report generation
- Set JSON file path, user query, and output preferences

Author: AI Development Team
Date: 2025-08-06
Version: 1.0
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from refine_synthesis_tool import RefineSynthesisTool

# ==========================================
# 📋 CONFIGURATION - EDIT THESE SETTINGS
# ==========================================

CONFIG = {
    # Input Configuration
    "json_file_path": "inputs/output_testing/test_03_3_get_full_file___pdf.json",
    
    # Query Configuration
    "user_query": "write me a detailed report on 'Risk Based Capital Requirements for Market Risk'",
    
    # Output Configuration
    "output_filename": "AI_Generated_Report",  # Will be appended with timestamp
    "report_title": "Risk Based Capital Requirements for Market Risk",
    "report_subtitle": "Detailed Analysis Report",
    
    # Processing Configuration
    "prioritize_chunks": True,  # Whether to reorder chunks by relevance
    "include_metadata": True,   # Whether to include processing metadata
    "include_processing_log": True,  # Whether to include detailed processing steps
    
    # Environment Configuration
    "env_file_path": "../.env",  # Path to .env file containing API key
    "api_key_name": "gemini_api_key",  # Name of API key variable in .env
}

# ==========================================
# 🚀 MAIN PROCESSING FUNCTION
# ==========================================

def generate_ai_report():
    """
    Generate AI-powered report based on configuration.
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Load environment variables
    load_dotenv(CONFIG["env_file_path"])
    
    # Generate output filename with timestamp
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{CONFIG['output_filename']}_{timestamp_str}.md"
    
    print("🤖 Generic AI Report Generator")
    print("="*60)
    print(f"📄 Input File: {CONFIG['json_file_path']}")
    print(f"❓ User Query: {CONFIG['user_query']}")
    print(f"📝 Output File: {output_file}")
    print(f"🏷️  Report Title: {CONFIG['report_title']}")
    
    # Validate input file exists
    if not os.path.exists(CONFIG["json_file_path"]):
        print(f"❌ Error: Input file not found: {CONFIG['json_file_path']}")
        return False
    
    # Load and analyze input data
    with open(CONFIG["json_file_path"], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📊 Input Analysis:")
    print(f"   Test ID: {data.get('test_id', 'N/A')}")
    print(f"   Test Name: {data.get('test_name', 'N/A')}")
    print(f"   Status: {data.get('status', 'N/A')}")
    
    # Get API key
    api_key = os.getenv(CONFIG["api_key_name"])
    if not api_key:
        print(f"❌ Error: {CONFIG['api_key_name']} not found in environment")
        print(f"   Check .env file at: {CONFIG['env_file_path']}")
        return False
    
    # Initialize tool and process
    try:
        print(f"\n🔄 Processing with Refine Synthesis Tool...")
        
        tool = RefineSynthesisTool(api_key=api_key)
        result = tool.process_json_file(
            CONFIG["json_file_path"], 
            CONFIG["user_query"]
        )
        
        # Generate markdown report
        markdown_content = generate_markdown_report(result, data, CONFIG)
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Report generated successfully!")
        print(f"📄 Saved: {output_file}")
        print(f"📊 Strategy: {result['metadata']['processing_strategy']}")
        print(f"⏱️  Processing time: {result['metadata']['total_processing_time']:.2f}s")
        print(f"📦 Chunks processed: {result['metadata']['total_chunks']}")
        print(f"🔢 Estimated tokens: {result['metadata']['total_tokens_estimated']:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_markdown_report(result, original_data, config):
    """
    Generate formatted markdown report from processing results.
    
    Args:
        result: Processing results from refine synthesis tool
        original_data: Original JSON data
        config: Configuration dictionary
    
    Returns:
        str: Formatted markdown content
    """
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Build markdown content
    markdown = f"""# {config['report_title']}
**{config['report_subtitle']} - AI Generated**

---

## 📋 Report Metadata

| Field | Value |
|-------|-------|
| **Generated** | {timestamp} |
| **Source File** | {original_data.get('test_params', {}).get('filename', 'N/A')} |
| **Input Query** | {config['user_query']} |
| **Processing Strategy** | {result['metadata']['processing_strategy']} |
| **Total Chunks Processed** | {result['metadata']['total_chunks']} |
| **Processing Time** | {result['metadata']['total_processing_time']:.2f} seconds |
| **Model Used** | {result['config']['model_name']} |

---

## 📖 Executive Summary

This report provides a comprehensive AI-generated analysis based on the retrieved document content, processed using advanced language model synthesis with quality assessment.

---

## 📄 AI-Generated Analysis

{result['response']}

---
"""
    
    # Add technical details if enabled
    if config.get("include_metadata", True):
        markdown += f"""
## 🔧 Technical Processing Details

### Processing Configuration
- **Chunk Prioritization**: {"Enabled" if result['metadata'].get('prioritized', True) else "Disabled"}
- **Total Batches**: {result['metadata']['total_batches']}
- **Estimated Tokens**: {result['metadata']['total_tokens_estimated']:,}
- **Max Content Tokens**: {result['config']['max_content_tokens']:,}
- **Chunks per Batch Limit**: {result['config']['chunks_per_batch_limit']}
"""
    
    # Add processing log if enabled
    if config.get("include_processing_log", True):
        markdown += f"""
### Processing Log
"""
        for i, log_entry in enumerate(result['processing_log'], 1):
            markdown += f"""
#### Step {i}: {log_entry['action'].replace('_', ' ').title()}
- **Batch Number**: {log_entry['batch_number']}
- **Chunks Processed**: {log_entry['chunk_count']}
- **Processing Duration**: {log_entry['processing_time']:.3f} seconds
"""
    
    # Add source information
    markdown += f"""
---

## 📚 Source Information

### Original Test Data
- **Test ID**: {original_data.get('test_id', 'N/A')}
- **Test Name**: {original_data.get('test_name', 'N/A')}
- **Test Operation**: {original_data.get('test_params', {}).get('operation', 'N/A')}
- **Processing Status**: {original_data.get('status', 'N/A')}

### Generation Details
- **Generated By**: Generic AI Report Generator v1.0
- **Configuration File**: See CONFIG section in script
- **Timestamp**: {timestamp}

---

*This report was generated using the Generic Report Generator with Refine Synthesis Tool and Gemini AI.*
"""
    
    return markdown


# ==========================================
# 🎯 EXAMPLE CONFIGURATIONS
# ==========================================

def show_example_configs():
    """Display example configurations for different use cases."""
    
    examples = {
        "Market Risk Analysis": {
            "json_file_path": "inputs/output_testing/test_03_3_get_full_file___pdf.json",
            "user_query": "write me a detailed report on 'Risk Based Capital Requirements for Market Risk'",
            "output_filename": "Market_Risk_Report",
            "report_title": "Risk Based Capital Requirements for Market Risk",
        },
        
        "File Discovery Summary": {
            "json_file_path": "inputs/output_testing/test_01_1_file_discovery.json",
            "user_query": "Provide a comprehensive summary of available files and their contents",
            "output_filename": "File_Discovery_Report",
            "report_title": "Document Repository Analysis",
        },
        
        "OSFI Search Analysis": {
            "json_file_path": "inputs/output_testing/test_02_2_search_content___valid.json",
            "user_query": "Analyze OSFI regulatory requirements and provide key insights",
            "output_filename": "OSFI_Analysis_Report",
            "report_title": "OSFI Regulatory Requirements Analysis",
        },
        
        "Excel Data Analysis": {
            "json_file_path": "inputs/output_testing/test_14_14_natural_language_test___excel_data.json",
            "user_query": "Analyze the financial data and provide insights on company performance",
            "output_filename": "Financial_Analysis_Report", 
            "report_title": "Financial Performance Analysis",
        },
        
        "Specific Page Analysis": {
            "json_file_path": "inputs/output_testing/test_13_13_natural_language_test___specific_page.json",
            "user_query": "Explain the regulatory requirements in detail with practical implications",
            "output_filename": "Regulatory_Page_Analysis",
            "report_title": "Detailed Regulatory Requirements Analysis",
        }
    }
    
    print("\n📋 Example Configurations:")
    print("="*60)
    
    for name, config in examples.items():
        print(f"\n🔹 {name}:")
        for key, value in config.items():
            print(f"   {key}: {value}")


# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================

def main():
    """Main execution function with configuration display."""
    
    print("🤖 Generic AI Report Generator")
    print("="*80)
    print("📝 Edit the CONFIG section in this script to customize report generation")
    
    # Show current configuration
    print(f"\n📋 Current Configuration:")
    print("-" * 40)
    for key, value in CONFIG.items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        print(f"{key:20}: {value}")
    
    print(f"\n🚀 Starting report generation...")
    
    success = generate_ai_report()
    
    if success:
        print(f"\n🎉 Report generation completed successfully!")
        print(f"📋 Next Steps:")
        print(f"   1. Open the generated .md file in a markdown viewer")
        print(f"   2. Review the AI-generated analysis")
        print(f"   3. Customize CONFIG section for different reports")
    else:
        print(f"\n❌ Report generation failed")
        print(f"📋 Troubleshooting:")
        print(f"   1. Check if input file exists")
        print(f"   2. Verify API key in .env file")
        print(f"   3. Ensure dependencies are installed")
    
    # Show example configurations
    show_example_configs()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())