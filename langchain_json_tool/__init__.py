"""
LangChain JSON Search Tool Package
=================================

This package provides LangChain tools for searching and fetching data from
processed JSON documents (PDFs, Excel, CSV files).

Available Tools:
1. JSONSearchTool - Direct search operations (discover, search_content, get_full_file, etc.)
2. IntegratedDiscoverySynthesisTool - Complete flow with discovery, search, and AI synthesis

Usage:
    # Basic search tool
    from langchain_json_tool import create_json_search_tool
    tool = create_json_search_tool("../Fetch_data/unified_results.json")
    result = tool._run(operation="discover")
    
    # Integrated discovery and synthesis tool (recommended)
    from langchain_json_tool import create_integrated_discovery_synthesis_tool
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    result = tool._run(user_query="What are the capital requirements?")
"""

from .langchain_json_searcher_tool import JSONSearchTool, create_json_search_tool, JSONSearchInput

# Import integrated tool separately to avoid circular imports
try:
    from .integrated_discovery_synthesis_tool import IntegratedDiscoverySynthesisTool, create_integrated_discovery_synthesis_tool, IntegratedDiscoverySynthesisInput
except ImportError as e:
    print(f"Warning: Could not import integrated discovery synthesis tool: {e}")
    IntegratedDiscoverySynthesisTool = None
    create_integrated_discovery_synthesis_tool = None
    IntegratedDiscoverySynthesisInput = None

__version__ = "1.0.0"
__author__ = "AI Assistant"
__all__ = [
    "JSONSearchTool", 
    "create_json_search_tool", 
    "JSONSearchInput",
    "IntegratedDiscoverySynthesisTool",
    "create_integrated_discovery_synthesis_tool", 
    "IntegratedDiscoverySynthesisInput"
]