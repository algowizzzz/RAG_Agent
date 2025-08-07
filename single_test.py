#!/usr/bin/env python3
"""
Single Question Test with Document Source Extraction
===================================================

This script tests a single question to verify document source extraction
and displays the full retrieval details.
"""

import json
from datetime import datetime
from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool

def main():
    print("🔍 Single Question Test - Document Source Tracking")
    print("=" * 60)
    
    # Test question
    question = "As a assistant to cfo, review the Show me the Balance Sheet data from the techtrends Excel file"
    print(f"❓ Question: {question}")
    print("=" * 60)
    
    # Initialize tool
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    print("✅ Tool initialized")
    
    # Process the question
    start_time = datetime.now()
    result = tool._run(
        user_query=question,
        include_reasoning=True,
        max_results=20
    )
    end_time = datetime.now()
    
    result_data = json.loads(result)
    
    print(f"\n📊 RESULTS:")
    print(f"Status: {result_data['status']}")
    print(f"Processing Time: {(end_time - start_time).total_seconds():.2f}s")
    
    if result_data['status'] == 'SUCCESS':
        print(f"Strategy: {result_data['processing_summary']['processing_strategy']}")
        print(f"Chunks: {result_data['processing_summary']['total_chunks_processed']}")
        
        # Extract and display document sources
        print(f"\n📚 DOCUMENT SOURCES ANALYSIS:")
        
        if 'detailed_reasoning' in result_data:
            reasoning = result_data['detailed_reasoning']
            print(f"✅ Detailed reasoning available")
            
            # Check discovery results
            if 'discovery_results' in reasoning:
                discovery = reasoning['discovery_results']
                print(f"\n🔍 DISCOVERY RESULTS:")
                print(f"Available documents: {len(discovery.get('available_documents', []))}")
                for i, doc in enumerate(discovery.get('available_documents', [])[:5]):
                    print(f"  {i+1}. {doc.get('filename', 'Unknown')} ({doc.get('content_type', 'Unknown')})")
            
            # Check LLM decision process
            if 'llm_decision_making_process' in reasoning:
                print(f"\n🧠 LLM DECISION PROCESS:")
                for step in reasoning['llm_decision_making_process']:
                    phase = step.get('phase', 'Unknown')
                    print(f"  - Phase: {phase}")
                    
                    if phase == 'content_retrieval' and 'retrieved_content' in step:
                        print(f"    Retrieved chunks: {len(step['retrieved_content'])}")
                        for i, chunk in enumerate(step['retrieved_content'][:3]):
                            source_file = chunk.get('source_file', 'Unknown')
                            page = chunk.get('page', 'N/A')
                            score = chunk.get('relevance_score', 0)
                            print(f"      {i+1}. {source_file} (page {page}, score: {score:.3f})")
                    
                    elif phase == 'discovery_and_metadata':
                        if 'discovery_results' in step:
                            docs = step['discovery_results'].get('available_documents', [])
                            print(f"    Discovered documents: {len(docs)}")
        else:
            print("❌ No detailed reasoning available")
        
        # Show answer preview
        print(f"\n📝 ANSWER PREVIEW:")
        answer = result_data['ai_response']
        print(f"{answer[:500]}...")
        
    else:
        print(f"❌ Error: {result_data.get('error_message', 'Unknown')}")

if __name__ == "__main__":
    main()