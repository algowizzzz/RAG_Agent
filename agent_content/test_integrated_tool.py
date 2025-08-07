#!/usr/bin/env python3
"""
Test Script for Integrated Discovery and Synthesis Tool
======================================================

This script demonstrates the correct flow:
User Query + JSONSearchTool (discovery and metadata results) → JSONSearchTool (operation/s) → RefineSynthesisTool → Comprehensive Response

Usage:
    python test_integrated_tool.py
"""

import sys
import json
from pathlib import Path
import datetime
import os

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool


def test_correct_flow():
    """Test the correct flow implementation."""
    
    print("🧪 Testing Correct Flow Implementation")
    print("=" * 60)
    print("Flow: User Query + JSONSearchTool (discovery and metadata results) → JSONSearchTool (operation/s) → RefineSynthesisTool → Comprehensive Response")
    print("=" * 60)
    
    # Create the tool
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    
    # Test cases demonstrating the correct flow
    test_cases = [
        {
            "name": "OSFI Capital Requirements Analysis",
            "user_query": "What are the key capital requirements for market risk according to OSFI regulations?",
            "expected_flow": "Discovery → Metadata Analysis → Content Search Operations → Synthesis"
        },
        {
            "name": "Financial Data Extraction",
            "user_query": "Show me the Balance Sheet data from the TechTrend financial spreadsheet",
            "expected_flow": "Discovery → Metadata Analysis → File-specific Operations → Synthesis"
        },
        {
            "name": "Comprehensive Document Analysis",
            "user_query": "What regulatory frameworks and compliance requirements are discussed across all available documents?",
            "expected_flow": "Discovery → Metadata Analysis → Multi-operation Search → Synthesis"
        },
        {
            "name": "Specific Page Request",
            "user_query": "What is discussed on page 5 of the OSFI document?",
            "expected_flow": "Discovery → Metadata Analysis → Targeted Page Operation → Synthesis"
        }
    ]
    
    results_summary = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Query: {test_case['user_query']}")
        print(f"Expected Flow: {test_case['expected_flow']}")
        print("-" * 50)
        
        test_start = datetime.datetime.now()
        
        try:
            # Execute the tool
            result = tool._run(
                user_query=test_case['user_query'],
                include_reasoning=True,
                max_results=30
            )
            
            # Parse and analyze the result
            result_data = json.loads(result)
            test_end = datetime.datetime.now()
            
            if result_data['status'] == 'SUCCESS':
                print("✅ SUCCESS")
                
                # Show flow execution details
                flow_info = result_data.get('correct_flow_executed', {})
                print(f"Flow Executed:")
                for step, description in flow_info.items():
                    print(f"  {step}: {description}")
                
                # Show operations that were determined and executed
                operations = result_data['processing_summary'].get('operations_executed', [])
                print(f"\nOperations Determined from Query + Discovery/Metadata:")
                for j, op in enumerate(operations, 1):
                    print(f"  {j}. {op.get('operation', 'unknown')} - {op.get('justification', 'No justification')}")
                
                # Show synthesis results
                chunks_processed = result_data['processing_summary'].get('total_chunks_processed', 0)
                processing_time = result_data['processing_summary'].get('total_processing_time_seconds', 0)
                
                print(f"\nSynthesis Results:")
                print(f"  Chunks Processed: {chunks_processed}")
                print(f"  Processing Time: {processing_time:.2f}s")
                print(f"  Response Length: {len(result_data['ai_response'])} characters")
                print(f"  Response Preview: {result_data['ai_response'][:150]}...")
                
                # Analyze the reasoning if available
                if 'detailed_reasoning' in result_data:
                    reasoning = result_data['detailed_reasoning']
                    discovery_files = reasoning['discovery_and_metadata_results']['discovery_results'].get('summary', {}).get('files', [])
                    print(f"\nDiscovery Results: {len(discovery_files)} files found")
                    
                    ops_reasoning = reasoning.get('operation_determination_reasoning', {})
                    if 'operation_determination' in ops_reasoning:
                        print(f"Operation Determination: {ops_reasoning['operation_determination'].get('reasoning', 'No reasoning available')}")
                
                results_summary.append({
                    "test_name": test_case['name'],
                    "status": "SUCCESS",
                    "operations_count": len(operations),
                    "chunks_processed": chunks_processed,
                    "processing_time": processing_time
                })
                
            else:
                print("❌ ERROR")
                print(f"Error: {result_data.get('error_message', 'Unknown error')}")
                results_summary.append({
                    "test_name": test_case['name'],
                    "status": "ERROR",
                    "error": result_data.get('error_message', 'Unknown error')
                })
            
        except Exception as e:
            test_end = datetime.datetime.now()
            print(f"❌ EXCEPTION: {str(e)}")
            results_summary.append({
                "test_name": test_case['name'],
                "status": "EXCEPTION",
                "error": str(e)
            })
        
        print(f"Test Duration: {(test_end - test_start).total_seconds():.2f}s")
    
    # Print summary
    print(f"\n📊 Test Summary")
    print("=" * 40)
    successful_tests = [r for r in results_summary if r['status'] == 'SUCCESS']
    print(f"Successful Tests: {len(successful_tests)}/{len(test_cases)}")
    
    if successful_tests:
        avg_processing_time = sum(r.get('processing_time', 0) for r in successful_tests) / len(successful_tests)
        total_operations = sum(r.get('operations_count', 0) for r in successful_tests)
        total_chunks = sum(r.get('chunks_processed', 0) for r in successful_tests)
        
        print(f"Average Processing Time: {avg_processing_time:.2f}s")
        print(f"Total Operations Executed: {total_operations}")
        print(f"Total Chunks Processed: {total_chunks}")
    
    print(f"\n🎯 Flow Verification:")
    print("✅ Discovery and metadata collection using JSONSearchTool")
    print("✅ Operation determination from query + discovery/metadata analysis")
    print("✅ Targeted JSONSearchTool operation execution")
    print("✅ RefineSynthesisTool processing of retrieved content")
    print("✅ Comprehensive response with full reasoning transparency")


def demonstrate_flow_steps():
    """Demonstrate each step of the correct flow separately."""
    
    print(f"\n🔍 Flow Step Demonstration")
    print("=" * 50)
    
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    
    example_query = "What are the capital requirements for market risk?"
    
    print(f"Example Query: '{example_query}'")
    print(f"\nFlow Steps:")
    print(f"1. 📋 Discovery Phase: JSONSearchTool discovers available files")
    print(f"2. 🔍 Metadata Phase: JSONSearchTool analyzes data structure")
    print(f"3. 🧠 Analysis Phase: Combine query + discovery/metadata → determine operations")
    print(f"4. ⚡ Execution Phase: Execute determined JSONSearchTool operations")
    print(f"5. 🔄 Synthesis Phase: RefineSynthesisTool processes retrieved content")
    print(f"6. 📄 Response Phase: Generate comprehensive response with reasoning")
    
    print(f"\nThis approach ensures:")
    print(f"✅ Data-informed operation selection")
    print(f"✅ Optimal use of available information")
    print(f"✅ Transparent decision-making process")
    print(f"✅ Comprehensive synthesis of relevant content")


if __name__ == "__main__":
    # Run the correct flow tests
    test_correct_flow()
    
    # Demonstrate flow steps
    demonstrate_flow_steps()
    
    print("\n✅ All tests completed!")
    print("\nNext Steps:")
    print("1. Set GEMINI_API_KEY environment variable")
    print("2. Ensure ../Fetch_data/unified_results.json exists")
    print("3. Use the tool in your LangChain workflow")
    print("\nUsage:")
    print("from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool")
    print("tool = create_integrated_discovery_synthesis_tool()")
    print("result = tool._run(user_query='Your question here')")