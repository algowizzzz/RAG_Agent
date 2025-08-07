#!/usr/bin/env python3
"""
Test Script for LangChain JSON Search Tool
==========================================

This script demonstrates how to use the LangChain JSON Search Tool
with various operations and error handling.

Usage:
    python test_langchain_tool.py
"""

import sys
import json
from pathlib import Path
import datetime
import os

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from langchain_json_searcher_tool import JSONSearchTool, create_json_search_tool


def test_all_operations():
    """Test all tool operations with proper error handling and save results."""
    
    print("🧪 Testing LangChain JSON Search Tool")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("output_testing")
    output_dir.mkdir(exist_ok=True)
    
    # Create the tool
    tool = create_json_search_tool("../Fetch_data/unified_results.json")
    
    # Test session metadata
    test_session = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": []
    }
    
    # Test cases
    test_cases = [
        {
            "name": "1. File Discovery",
            "params": {"operation": "discover"},
            "expected": "Should list all available files"
        },
        {
            "name": "2. Search Content - Valid",
            "params": {
                "operation": "search_content", 
                "search_value": "OSFI",
                "search_type": "partial"
            },
            "expected": "Should find content matches for 'OSFI'"
        },
        {
            "name": "3. Get Full File - PDF", 
            "params": {
                "operation": "get_full_file",
                "filename": "car24_chpt1_0.pdf"
            },
            "expected": "Should retrieve all PDF chunks"
        },
        {
            "name": "4. Get Single Item - Specific Page",
            "params": {
                "operation": "get_single_item",
                "filename": "car24_chpt1_0.pdf", 
                "page": 5
            },
            "expected": "Should retrieve page 5 content"
        },
        {
            "name": "5. Search Metadata - By Filename",
            "params": {
                "operation": "search_metadata",
                "search_value": "car24_chpt1_0.pdf",
                "field": "source_file", 
                "search_type": "exact"
            },
            "expected": "Should find metadata for PDF file"
        },
        {
            "name": "6. Get Excel Sheet",
            "params": {
                "operation": "get_single_item",
                "filename": "TechTrend_Financials_2024.xlsx",
                "sheet": "Balance Sheet"
            },
            "expected": "Should retrieve Balance Sheet data"
        },
        {
            "name": "7. Error Test - Missing Parameter",
            "params": {
                "operation": "get_full_file"
                # Missing filename parameter
            },
            "expected": "Should return error for missing filename"
        },
        {
            "name": "8. Error Test - Invalid Operation",
            "params": {
                "operation": "invalid_operation"
            },
            "expected": "Should return error for invalid operation"
        },
        {
            "name": "9. Error Test - File Not Found",
            "params": {
                "operation": "get_full_file",
                "filename": "nonexistent_file.pdf"
            },
            "expected": "Should handle file not found gracefully"
        },
        {
            "name": "10. Search with Regex",
            "params": {
                "operation": "search_content",
                "search_value": "capital.*requirements",
                "search_type": "regex"
            },
            "expected": "Should find regex pattern matches"
        },
        {
            "name": "11. Natural Language Test - File Discovery",
            "params": {"operation": "discover"},
            "expected": "Natural language: What files are available in the dataset?"
        },
        {
            "name": "12. Natural Language Test - Content Search",
            "params": {
                "operation": "search_content",
                "search_value": "capital requirements",
                "search_type": "partial"
            },
            "expected": "Natural language: Find all mentions of capital requirements"
        },
        {
            "name": "13. Natural Language Test - Specific Page",
            "params": {
                "operation": "get_single_item",
                "filename": "car24_chpt1_0.pdf",
                "page": 5
            },
            "expected": "Natural language: Get page 5 from car24_chpt1_0.pdf"
        },
        {
            "name": "14. Natural Language Test - Excel Data",
            "params": {
                "operation": "get_single_item",
                "filename": "TechTrend_Financials_2024.xlsx",
                "sheet": "Balance Sheet"
            },
            "expected": "Natural language: Show me the Balance Sheet data from the techtrends Excel file"
        },
        {
            "name": "15. Natural Language Test - Word Count Analysis",
            "params": {"operation": "discover"},
            "expected": "Natural language: What is the total token count of all the words in attached file (uses discover to get file stats)"
        }
    ]
    
    # Run all test cases
    for i, test_case in enumerate(test_cases, 1):
        test_start_time = datetime.datetime.now()
        print(f"\n{test_case['name']}")
        print("-" * 40)
        print(f"Expected: {test_case['expected']}")
        print(f"Parameters: {json.dumps(test_case['params'], indent=2)}")
        
        # Test result structure
        test_result = {
            "test_id": i,
            "test_name": test_case['name'],
            "test_params": test_case['params'],
            "expected": test_case['expected'],
            "start_time": test_start_time.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "status": "UNKNOWN",
            "passed": False,
            "response": None,
            "error_info": None,
            "summary": None
        }
        
        try:
            # Run the test
            result = tool._run(**test_case['params'])
            test_end_time = datetime.datetime.now()
            test_result["end_time"] = test_end_time.isoformat()
            test_result["duration_seconds"] = (test_end_time - test_start_time).total_seconds()
            
            # Parse result to get status
            result_dict = json.loads(result)
            test_result["response"] = result_dict
            status = result_dict.get('summary', {}).get('status', 'UNKNOWN')
            if status == 'ERROR':
                status = result_dict.get('status', 'ERROR')
            
            test_result["status"] = status
            print(f"Result Status: {status}")
            
            # Show summary for successful operations
            if status == 'SUCCESS':
                test_result["passed"] = True
                test_session["passed_tests"] += 1
                summary_info = test_result["response"].get('summary', {}).get('summary', 'No summary')
                test_result["summary"] = summary_info
                print(f"Summary: {summary_info}")
                
                # Show first few results for searches
                detailed = test_result["response"].get('detailed_results', {})
                if 'total_results' in detailed and detailed['total_results'] > 0:
                    print(f"Total Results: {detailed['total_results']}")
                    if 'results' in detailed and len(detailed['results']) > 0:
                        print(f"First Result Preview: {str(detailed['results'][0])[:100]}...")
                        
            # Show error details for failed operations
            elif status == 'ERROR':
                test_result["passed"] = False
                test_session["failed_tests"] += 1
                error_type = test_result["response"].get('error_type', 'Unknown')
                message = test_result["response"].get('message', 'No message')
                test_result["error_info"] = {
                    "error_type": error_type,
                    "message": message
                }
                print(f"Error Type: {error_type}")
                print(f"Error Message: {message}")
                
        except Exception as e:
            test_end_time = datetime.datetime.now()
            test_result["end_time"] = test_end_time.isoformat()
            test_result["duration_seconds"] = (test_end_time - test_start_time).total_seconds()
            test_result["status"] = "EXCEPTION"
            test_result["passed"] = False
            test_result["error_info"] = {
                "error_type": "Exception",
                "message": str(e)
            }
            test_session["failed_tests"] += 1
            print(f"Test Failed with Exception: {str(e)}")
        
        # Save individual test result
        test_filename = f"test_{i:02d}_{test_case['name'].replace(' ', '_').replace('.', '').replace('-', '_').lower()}.json"
        test_file_path = output_dir / test_filename
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved: {test_file_path}")
        test_session["test_results"].append(test_result)
    
    # Finalize session summary
    test_session["total_tests"] = len(test_cases)
    test_session["end_time"] = datetime.datetime.now().isoformat()
    
    # Save session summary
    session_file_path = output_dir / "test_session_summary.json"
    with open(session_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_session, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 Testing Complete!")
    print("=" * 60)
    print(f"📊 Results: {test_session['passed_tests']}/{test_session['total_tests']} tests passed")
    print(f"💾 All results saved to: {output_dir}")
    print(f"📄 Session summary: {session_file_path}")


def demo_langchain_integration():
    """Demonstrate how to use the tool with LangChain agents."""
    
    print("\n🤖 LangChain Integration Demo")
    print("=" * 60)
    
    # Create tool
    tool = create_json_search_tool()
    
    print("\nTool Information:")
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    
    # Show how tool would be used in a LangChain agent
    example_agent_usage = """
    from langchain.agents import initialize_agent, AgentType
    from langchain.llms import OpenAI  # or any other LLM
    
    # Create the tool
    json_search_tool = create_json_search_tool("path/to/unified_results.json")
    
    # Initialize agent with the tool
    llm = OpenAI(temperature=0)
    agent = initialize_agent(
        tools=[json_search_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    
    # Agent can now use the tool to answer questions like:
    response = agent.run("What files are available in the dataset?")
    response = agent.run("Find all mentions of 'capital requirements' in the documents")
    response = agent.run("Get the content from page 5 of the PDF document")
    """
    
    print("\nExample LangChain Agent Integration:")
    print(example_agent_usage)


def simple_demo():
    """Simple demonstration of basic tool functionality."""
    
    print("\n🎯 Simple Tool Demo")
    print("=" * 40)
    
    # Create tool
    tool = create_json_search_tool("../Fetch_data/unified_results.json")
    
    # Demo 1: Discover files
    print("\n1. Discovering files in dataset...")
    result = tool._run(operation="discover")
    print("✅ Files discovered!")
    
    # Demo 2: Search for content
    print("\n2. Searching for 'risk' in content...")
    result = tool._run(
        operation="search_content",
        search_value="risk",
        search_type="partial"
    )
    print("✅ Content search completed!")
    
    # Demo 3: Get specific page
    print("\n3. Getting page 1 from PDF...")
    result = tool._run(
        operation="get_single_item",
        filename="car24_chpt1_0.pdf",
        page=1
    )
    print("✅ Page retrieval completed!")


if __name__ == "__main__":
    # Choose demo mode based on command line args
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        simple_demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "integration":
        demo_langchain_integration()
    else:
        # Run comprehensive tests
        test_all_operations()
        
        # Show integration example
        demo_langchain_integration()
    
    print("\n✅ All demos completed!")
    print("\nNext Steps:")
    print("1. Install dependencies: pip install langchain langchain-community")
    print("2. Use the tool in your LangChain workflow")
    print("3. Test with real queries relevant to your documents")
    print("\nRun modes:")
    print("- python test_langchain_tool.py          # Full test suite")
    print("- python test_langchain_tool.py simple   # Simple demo only")
    print("- python test_langchain_tool.py integration # Integration examples only")