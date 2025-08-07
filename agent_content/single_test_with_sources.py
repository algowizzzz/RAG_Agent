#!/usr/bin/env python3
"""
Single Question Test with Enhanced Document Source Tracking
==========================================================

This script tests document source extraction and creates a simple report
showing which files were used.
"""

import json
from datetime import datetime
from pathlib import Path
from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool

def extract_all_document_sources(result_data):
    """Extract comprehensive document sources from any processing strategy."""
    sources = []
    
    try:
        # 1. Check detailed reasoning for discovery results
        if 'detailed_reasoning' in result_data:
            reasoning = result_data['detailed_reasoning']
            
            # Discovery phase documents
            if 'discovery_results' in reasoning:
                discovery = reasoning['discovery_results']
                if 'available_documents' in discovery:
                    for doc in discovery['available_documents']:
                        sources.append({
                            'filename': doc.get('filename', 'Unknown'),
                            'content_type': doc.get('content_type', 'Unknown'),
                            'page_count': doc.get('page_count', 'N/A'),
                            'source_type': 'Available Document'
                        })
            
            # LLM decision process
            if 'llm_decision_making_process' in reasoning:
                for step in reasoning['llm_decision_making_process']:
                    # Discovery and metadata phase
                    if step.get('phase') == 'discovery_and_metadata' and 'discovery_results' in step:
                        discovery = step['discovery_results']
                        if 'available_documents' in discovery:
                            for doc in discovery['available_documents']:
                                sources.append({
                                    'filename': doc.get('filename', 'Unknown'),
                                    'content_type': doc.get('content_type', 'Unknown'),
                                    'page_count': doc.get('page_count', 'N/A'),
                                    'source_type': 'Discovered Document'
                                })
                    
                    # Content retrieval phase (for retrieval_synthesis strategy)
                    elif step.get('phase') == 'content_retrieval' and 'retrieved_content' in step:
                        for chunk in step['retrieved_content']:
                            sources.append({
                                'filename': chunk.get('source_file', 'Unknown'),
                                'page': chunk.get('page', 'N/A'),
                                'relevance_score': chunk.get('relevance_score', 0),
                                'source_type': 'Retrieved Chunk'
                            })
                    
                    # Direct synthesis phase - check if chunk info is available
                    elif step.get('phase') == 'direct_synthesis' and 'chunks_used' in step:
                        for chunk in step['chunks_used']:
                            sources.append({
                                'filename': chunk.get('source_file', 'Unknown'),
                                'page': chunk.get('page', 'N/A'),
                                'source_type': 'Direct Synthesis Chunk'
                            })
        
        # 2. Check processing summary for additional sources
        if 'processing_summary' in result_data:
            summary = result_data['processing_summary']
            if 'source_files_used' in summary:
                for file_info in summary['source_files_used']:
                    sources.append({
                        'filename': file_info.get('filename', 'Unknown'),
                        'chunks_count': file_info.get('chunks_count', 0),
                        'source_type': 'Processing Summary'
                    })
        
        # Remove duplicates and return
        unique_sources = []
        seen = set()
        for source in sources:
            key = source.get('filename', 'Unknown')
            if key not in seen:
                seen.add(key)
                unique_sources.append(source)
        
        return unique_sources
        
    except Exception as e:
        print(f"⚠️  Error extracting sources: {e}")
        return []

def main():
    print("🔍 Enhanced Document Source Test")
    print("=" * 50)
    
    # Test question
    question = "As a assistant to cfo, review the Show me the Balance Sheet data from the techtrends Excel file"
    print(f"❓ Question: {question}")
    print("=" * 50)
    
    # Initialize tool
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    print("✅ Tool initialized")
    
    # Process the question
    result = tool._run(
        user_query=question,
        include_reasoning=True,
        max_results=20
    )
    
    result_data = json.loads(result)
    
    if result_data['status'] == 'SUCCESS':
        print(f"\n📊 Processing Strategy: {result_data['processing_summary']['processing_strategy']}")
        
        # Extract document sources
        sources = extract_all_document_sources(result_data)
        
        print(f"\n📚 DOCUMENT SOURCES FOUND ({len(sources)}):")
        print("-" * 50)
        
        if sources:
            for i, source in enumerate(sources, 1):
                filename = source.get('filename', 'Unknown')
                source_type = source.get('source_type', 'Unknown')
                
                print(f"{i}. {filename}")
                print(f"   Type: {source_type}")
                
                if 'content_type' in source:
                    print(f"   Content: {source['content_type']}")
                if 'page_count' in source:
                    print(f"   Pages: {source['page_count']}")
                if 'page' in source:
                    print(f"   Page: {source['page']}")
                if 'relevance_score' in source:
                    print(f"   Score: {source['relevance_score']:.3f}")
                print()
        else:
            print("❌ No document sources found")
        
        # Generate simple markdown with sources
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"output_reports/Single_Question_Report_{timestamp}.md"
        
        # Create output directory
        Path("output_reports").mkdir(exist_ok=True)
        
        # Generate report
        markdown_content = f"""# Single Question Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Question:** {question}
**Processing Strategy:** {result_data['processing_summary']['processing_strategy']}

## Document Sources Used

"""
        
        if sources:
            markdown_content += "| # | Document Name | Type | Details |\n"
            markdown_content += "|---|---------------|------|----------|\n"
            
            for i, source in enumerate(sources, 1):
                filename = source.get('filename', 'Unknown')
                source_type = source.get('source_type', 'Unknown')
                
                details = []
                if 'content_type' in source:
                    details.append(f"Content: {source['content_type']}")
                if 'page_count' in source:
                    details.append(f"Pages: {source['page_count']}")
                if 'page' in source:
                    details.append(f"Page: {source['page']}")
                if 'relevance_score' in source:
                    details.append(f"Score: {source['relevance_score']:.3f}")
                
                details_str = "; ".join(details) if details else "N/A"
                markdown_content += f"| {i} | {filename} | {source_type} | {details_str} |\n"
        else:
            markdown_content += "*No specific document sources captured*\n"
        
        markdown_content += f"""

## Answer

{result_data['ai_response']}

---
*Generated by Agent Content Package*
"""
        
        # Write report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"📄 Report saved: {report_file}")
        
    else:
        print(f"❌ Error: {result_data.get('error_message', 'Unknown')}")

if __name__ == "__main__":
    main()