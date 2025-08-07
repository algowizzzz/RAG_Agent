#!/usr/bin/env python3
"""
Single Question Runner with Document Source Tracking
==================================================

Runs one specific question and generates a markdown report with document sources.
"""

import json
from datetime import datetime
from pathlib import Path
from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool

def extract_document_sources(result_data):
    """Extract document sources from processing results."""
    sources = []
    
    try:
        if 'detailed_reasoning' in result_data:
            reasoning = result_data['detailed_reasoning']
            
            # Check LLM decision process for discovery results
            if 'llm_decision_making_process' in reasoning:
                for step in reasoning['llm_decision_making_process']:
                    if step.get('phase') == 'discovery_and_metadata' and 'discovery_results' in step:
                        discovery = step['discovery_results']
                        if 'available_documents' in discovery:
                            for doc in discovery['available_documents']:
                                sources.append({
                                    'filename': doc.get('filename', 'Unknown'),
                                    'content_type': doc.get('content_type', 'Unknown'),
                                    'page_count': doc.get('page_count', 'N/A'),
                                    'source_type': 'Available Document'
                                })
                    
                    # Check for retrieved content
                    elif step.get('phase') == 'content_retrieval' and 'retrieved_content' in step:
                        for chunk in step['retrieved_content'][:10]:  # Limit to top 10
                            sources.append({
                                'filename': chunk.get('source_file', 'Unknown'),
                                'page': chunk.get('page', 'N/A'),
                                'relevance_score': f"{chunk.get('relevance_score', 0):.3f}",
                                'source_type': 'Retrieved Chunk'
                            })
            
            # Also check direct discovery results
            if 'discovery_results' in reasoning:
                discovery = reasoning['discovery_results']
                if 'available_documents' in discovery:
                    for doc in discovery['available_documents']:
                        sources.append({
                            'filename': doc.get('filename', 'Unknown'),
                            'content_type': doc.get('content_type', 'Unknown'),
                            'page_count': doc.get('page_count', 'N/A'),
                            'source_type': 'Discovered Document'
                        })
        
        # Remove duplicates based on filename
        unique_sources = []
        seen_files = set()
        for source in sources:
            file_key = source.get('filename', 'Unknown')
            if file_key not in seen_files:
                seen_files.add(file_key)
                unique_sources.append(source)
        
        return unique_sources
        
    except Exception as e:
        print(f"⚠️  Warning: Could not extract document sources: {str(e)}")
        return []

def main():
    print("🔍 Single Question Analysis")
    print("=" * 60)
    
    # The specific question
    question = 'As a assistant to cfo, review the Show me the Balance Sheet data from the techtrends Excel file'
    print(f"❓ Question: {question}")
    print("=" * 60)
    
    # Initialize tool
    try:
        tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
        print("✅ Tool initialized")
    except Exception as e:
        print(f"❌ Error initializing tool: {str(e)}")
        return
    
    # Process the question
    print(f"\n🔄 Processing question...")
    start_time = datetime.now()
    
    try:
        result = tool._run(
            user_query=question,
            include_reasoning=True,
            max_results=30
        )
        
        result_data = json.loads(result)
        end_time = datetime.now()
        
        if result_data['status'] == 'SUCCESS':
            processing_time = result_data['processing_summary']['total_processing_time_seconds']
            chunks_processed = result_data['processing_summary']['total_chunks_processed']
            strategy = result_data['processing_summary']['processing_strategy']
            
            print(f"✅ Success!")
            print(f"📊 Strategy: {strategy}")
            print(f"⏱️  Time: {processing_time:.2f}s")
            print(f"📦 Chunks: {chunks_processed}")
            print(f"📝 Response: {len(result_data['ai_response'])} characters")
            
            # Extract document sources
            document_sources = extract_document_sources(result_data)
            print(f"📚 Sources: {len(document_sources)} documents")
            
            # Display sources
            if document_sources:
                print(f"\n📋 DOCUMENT SOURCES:")
                for i, source in enumerate(document_sources, 1):
                    filename = source.get('filename', 'Unknown')
                    source_type = source.get('source_type', 'Unknown')
                    print(f"  {i}. {filename} ({source_type})")
                    if 'content_type' in source:
                        print(f"     Content: {source['content_type']}")
                    if 'page_count' in source:
                        print(f"     Pages: {source['page_count']}")
            
            # Generate markdown report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"output_reports/CFO_Balance_Sheet_Analysis_{timestamp}.md"
            
            # Create output directory
            Path("output_reports").mkdir(exist_ok=True)
            
            # Generate comprehensive markdown report
            markdown_content = f"""# CFO Balance Sheet Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Question:** {question}  
**Processing Strategy:** {strategy}  
**Processing Time:** {processing_time:.2f} seconds  
**Chunks Processed:** {chunks_processed}  

## Document Sources Used

"""
            
            if document_sources:
                markdown_content += "| # | Document Name | Type | Details |\n"
                markdown_content += "|---|---------------|------|----------|\n"
                
                for i, source in enumerate(document_sources, 1):
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
                        details.append(f"Score: {source['relevance_score']}")
                    
                    details_str = "; ".join(details) if details else "N/A"
                    markdown_content += f"| {i} | {filename} | {source_type} | {details_str} |\n"
                    
                markdown_content += f"\n**Total Documents Referenced:** {len(document_sources)}\n\n"
            else:
                markdown_content += "*No specific document sources captured in this processing mode*\n\n"
            
            markdown_content += f"""## Analysis Response

{result_data['ai_response']}

## Technical Details

- **Processing Strategy:** {strategy}
- **Total Processing Time:** {processing_time:.2f} seconds
- **Chunks Processed:** {chunks_processed}
- **Response Length:** {len(result_data['ai_response']):,} characters
- **Status:** SUCCESS

---

*Report generated by Agent Content Package - Single Question Processor*
*Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
            
            # Write report
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"\n📄 Report saved: {report_file}")
            print(f"📊 Report contains {len(markdown_content):,} characters")
            print(f"✅ Single question analysis completed successfully!")
            
        else:
            print(f"❌ Failed: {result_data.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during processing: {str(e)}")

if __name__ == "__main__":
    main()