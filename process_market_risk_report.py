#!/usr/bin/env python3
"""
Market Risk Report Generator
===========================

This script processes the full PDF test file to generate a detailed report
on "Risk Based Capital Requirements for Market Risk" using the refine synthesis tool.

Usage:
    python3 process_market_risk_report.py

Output:
    Saves detailed report as .md file

Author: AI Development Team
Date: 2025-08-06
Version: 1.0
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Import refine synthesis tool (assuming it's in same directory)
try:
    from refine_synthesis_tool import RefineSynthesisTool
    TOOL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Refine tool not available: {e}")
    print("   Running in demo mode with mock output")
    TOOL_AVAILABLE = False


def process_market_risk_report():
    """Process the full PDF file and generate market risk report."""
    
    # Configuration
    json_file_path = "inputs/output_testing/test_03_3_get_full_file___pdf.json"
    user_query = "write me a detailed report on 'Risk Based Capital Requirements for Market Risk'"
    output_file = f"Market_Risk_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    print("🏦 Market Risk Report Generator")
    print("="*60)
    print(f"📄 Input: {json_file_path}")
    print(f"❓ Query: {user_query}")
    print(f"📝 Output: {output_file}")
    
    # Check if input file exists
    if not os.path.exists(json_file_path):
        print(f"❌ Error: Input file not found: {json_file_path}")
        return False
    
    # Load and analyze input data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📊 Input Analysis:")
    print(f"   Test ID: {data.get('test_id')}")
    print(f"   Test Name: {data.get('test_name')}")
    print(f"   Status: {data.get('status')}")
    
    # Get content details
    response_data = data.get('response', {})
    detailed_results = response_data.get('detailed_results', {})
    
    if 'chunks' in detailed_results:
        chunks = detailed_results['chunks']
        total_words = sum(chunk.get('words', 0) for chunk in chunks)
        print(f"   Chunks: {len(chunks)}")
        print(f"   Total Words: {total_words:,}")
    
    if TOOL_AVAILABLE:
        # Process with refine synthesis tool
        print(f"\n🔄 Processing with Refine Synthesis Tool...")
        
        try:
            # Check for API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️  GEMINI_API_KEY not found in environment")
                print("   Set API key: export GEMINI_API_KEY='your_key'")
                return generate_demo_report(data, user_query, output_file)
            
            # Initialize tool and process
            tool = RefineSynthesisTool(api_key=api_key)
            result = tool.process_json_file(json_file_path, user_query)
            
            # Generate markdown report
            markdown_content = generate_markdown_report(result, data, user_query)
            
            # Save report
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Report generated successfully!")
            print(f"📄 Saved: {output_file}")
            print(f"📊 Quality: {result['metadata']['processing_strategy']}")
            print(f"⏱️  Processing time: {result['metadata']['total_processing_time']:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing with tool: {str(e)}")
            return generate_demo_report(data, user_query, output_file)
    
    else:
        # Generate demo report without API
        return generate_demo_report(data, user_query, output_file)


def generate_markdown_report(result, original_data, user_query):
    """Generate formatted markdown report from refine synthesis result."""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    markdown = f"""# Risk Based Capital Requirements for Market Risk
**Detailed Analysis Report**

---

## 📋 Report Metadata

| Field | Value |
|-------|-------|
| **Generated** | {timestamp} |
| **Source Document** | car24_chpt1_0.pdf (OSFI CAR Chapter 1) |
| **Query** | {user_query} |
| **Processing Strategy** | {result['metadata']['processing_strategy']} |
| **Total Chunks Processed** | {result['metadata']['total_chunks']} |
| **Processing Time** | {result['metadata']['total_processing_time']:.2f} seconds |

---

## 📖 Executive Summary

This report provides a comprehensive analysis of Risk Based Capital Requirements for Market Risk based on the OSFI Capital Adequacy Requirements (CAR) guidelines, Chapter 1.

---

## 📄 Detailed Analysis

{result['response']}

---

## 🔧 Technical Processing Details

### Refine Synthesis Metadata
- **Total Batches**: {result['metadata']['total_batches']}
- **Chunk Prioritization**: {"Enabled" if result['metadata'].get('prioritized', True) else "Disabled"}
- **Estimated Tokens**: {result['metadata']['total_tokens_estimated']:,}

### Processing Log
"""
    
    # Add processing log
    for i, log_entry in enumerate(result['processing_log'], 1):
        markdown += f"""
#### Step {i}: {log_entry['action'].replace('_', ' ').title()}
- **Batch**: {log_entry['batch_number']}
- **Chunks**: {log_entry['chunk_count']}
- **Duration**: {log_entry['processing_time']:.3f}s
"""
    
    markdown += f"""
---

## 📚 Source Information

### Original Test Data
- **Test ID**: {original_data.get('test_id')}
- **Test Name**: {original_data.get('test_name')}
- **Source File**: {original_data.get('test_params', {}).get('filename', 'car24_chpt1_0.pdf')}
- **Operation**: {original_data.get('test_params', {}).get('operation', 'get_full_file')}

### Document Statistics
"""
    
    # Add document statistics if available
    detailed_results = original_data.get('response', {}).get('detailed_results', {})
    if 'chunks' in detailed_results:
        chunks = detailed_results['chunks']
        total_words = sum(chunk.get('words', 0) for chunk in chunks)
        markdown += f"""
- **Total Chunks**: {len(chunks)}
- **Total Words**: {total_words:,}
- **Average Words per Chunk**: {total_words/len(chunks):.0f}
"""
    
    markdown += f"""
---

## ⚙️ Generation Details

This report was generated using the Refine Synthesis Tool with the following configuration:
- **Model**: {result['config']['model_name']}
- **Max Content Tokens**: {result['config']['max_content_tokens']:,}
- **Chunks per Batch Limit**: {result['config']['chunks_per_batch_limit']}

**Generated by**: Market Risk Report Generator v1.0  
**Timestamp**: {timestamp}
"""
    
    return markdown


def generate_demo_report(data, user_query, output_file):
    """Generate a demo report without API calls."""
    
    print(f"\n📄 Generating demo report without API...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract some content info
    detailed_results = data.get('response', {}).get('detailed_results', {})
    chunks_info = ""
    
    if 'chunks' in detailed_results:
        chunks = detailed_results['chunks']
        total_words = sum(chunk.get('words', 0) for chunk in chunks)
        chunks_info = f"""
### Document Analysis
- **Total Chunks**: {len(chunks)}
- **Total Words**: {total_words:,}
- **Average Words per Chunk**: {total_words/len(chunks):.0f}

### Content Preview
Based on the OSFI CAR Chapter 1 document, this report would cover:
"""
        
        # Show first few chunks as preview
        for i, chunk in enumerate(chunks[:3]):
            content_preview = chunk.get('content', '')[:200] + "..." if len(chunk.get('content', '')) > 200 else chunk.get('content', '')
            chunks_info += f"""
#### Chunk {i+1} (Page {chunk.get('page_number', 'N/A')})
{content_preview}
"""
    
    demo_markdown = f"""# Risk Based Capital Requirements for Market Risk
**Detailed Analysis Report (Demo Version)**

---

## 📋 Report Metadata

| Field | Value |
|-------|-------|
| **Generated** | {timestamp} |
| **Source Document** | car24_chpt1_0.pdf (OSFI CAR Chapter 1) |
| **Query** | {user_query} |
| **Mode** | Demo (API key required for full processing) |

---

## 📖 Executive Summary

This is a demo report showing the structure and format that would be generated by the Refine Synthesis Tool. To generate the actual detailed analysis, please:

1. Set your Gemini API key: `export GEMINI_API_KEY='your_key'`
2. Install dependencies: `pip install -r requirements_refine.txt`
3. Run the script again

---

## 📄 Expected Analysis Structure

The full report would include:

### 1. Market Risk Framework Overview
- Definition and scope of market risk under OSFI CAR
- Regulatory requirements for market risk capital

### 2. Risk-Weighted Assets Calculation
- Standardized approach for market risk
- Internal models approach requirements
- Trading book vs banking book distinctions

### 3. Capital Requirements
- Minimum capital ratios for market risk
- Buffer requirements and adjustments
- Supervisory expectations

### 4. Implementation Guidelines
- Approval processes for internal models
- Monitoring and compliance requirements
- Reporting obligations

{chunks_info}

---

## 🔧 To Generate Full Report

```bash
# Set API key
export GEMINI_API_KEY='your_gemini_api_key'

# Install dependencies
pip install -r requirements_refine.txt

# Run generator
python3 process_market_risk_report.py
```

---

**Generated by**: Market Risk Report Generator v1.0 (Demo Mode)  
**Timestamp**: {timestamp}
"""
    
    # Save demo report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(demo_markdown)
    
    print(f"✅ Demo report generated!")
    print(f"📄 Saved: {output_file}")
    print(f"💡 Set GEMINI_API_KEY for full processing")
    
    return True


def main():
    """Main execution function."""
    
    print("🚀 Starting Market Risk Report Generation")
    
    success = process_market_risk_report()
    
    if success:
        print(f"\n🎉 Report generation completed successfully!")
        print(f"📋 Next steps:")
        print(f"   1. Review the generated .md file")
        print(f"   2. Open in markdown viewer for formatted display")
        print(f"   3. Use for regulatory analysis and compliance")
        return 0
    else:
        print(f"\n❌ Report generation failed")
        return 1


if __name__ == "__main__":
    exit(main())