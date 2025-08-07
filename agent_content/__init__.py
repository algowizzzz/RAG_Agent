"""
Agent Content Package
====================

This package contains the integrated LangChain tools for document discovery, search, and AI synthesis.

Components:
- JSONSearchTool: Direct search operations on processed documents
- IntegratedDiscoverySynthesisTool: Complete flow with discovery, search, and synthesis
- RefineSynthesisTool: AI-powered content synthesis using Gemini API

Usage:
    from agent_content import create_integrated_discovery_synthesis_tool
    
    tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
    result = tool._run(user_query="What are the capital requirements?")
"""

from .langchain_json_searcher_tool import JSONSearchTool, create_json_search_tool, JSONSearchInput
from .integrated_discovery_synthesis_tool import (
    IntegratedDiscoverySynthesisTool, 
    create_integrated_discovery_synthesis_tool, 
    IntegratedDiscoverySynthesisInput
)
from .refine_synthesis_tool import RefineSynthesisTool, RefineConfig

__version__ = "1.0.0"
__author__ = "AI Development Team"
__all__ = [
    "JSONSearchTool", 
    "create_json_search_tool", 
    "JSONSearchInput",
    "IntegratedDiscoverySynthesisTool",
    "create_integrated_discovery_synthesis_tool", 
    "IntegratedDiscoverySynthesisInput",
    "RefineSynthesisTool",
    "RefineConfig"
]