#!/usr/bin/env python3
"""
LangChain Tool for JSON Search and Data Fetching
================================================

This tool wraps the json_searcher.py functionality into a LangChain BaseTool 
that can be used with LangChain agents and workflows.

The tool provides 5 core search functions:
1. File Discovery - List all available files
2. Full File Results - Get complete content from a specific file  
3. Single Results - Get specific page/sheet from a file
4. Search Metadata - Search in file metadata (NOT content)
5. Search Content - Search in actual document text

Author: AI Assistant
Date: 2025-08-06
"""

import json
import os
from typing import Optional, Type, Dict, Any, Union
from pathlib import Path

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validator

# Import the searcher functions
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from Fetch_data.json_searcher import (
    discover_files,
    get_full_file, 
    get_single_item,
    search_metadata,
    search_content
)


class JSONSearchInput(BaseModel):
    """Input schema for the JSON Search Tool."""
    
    operation: str = Field(
        ...,
        description="The search operation to perform. Options: 'discover', 'get_full_file', 'get_single_item', 'search_metadata', 'search_content'"
    )
    
    json_file_path: str = Field(
        default="../Fetch_data/unified_results.json",
        description="Path to the JSON file to search. Default: '../Fetch_data/unified_results.json'"
    )
    
    filename: Optional[str] = Field(
        None,
        description="Target filename for file-specific operations (required for get_full_file, get_single_item)"
    )
    
    search_value: Optional[Union[str, int]] = Field(
        None,
        description="Value to search for (required for search_metadata, search_content)"
    )
    
    field: Optional[str] = Field(
        None,
        description="Specific metadata field to search in (for search_metadata). Examples: 'source_file', 'page_number', 'processing_timestamp'"
    )
    
    search_type: str = Field(
        default="partial",
        description="Search type: 'exact', 'partial', or 'regex'. Default: 'partial'"
    )
    
    page: Optional[int] = Field(
        None,
        description="Page number for PDF content (for get_single_item)"
    )
    
    sheet: Optional[str] = Field(
        None,
        description="Sheet name for Excel content (for get_single_item)"
    )
    
    chunk: Optional[int] = Field(
        None,
        description="Chunk index for PDF content (for get_single_item)"
    )

    @validator('operation')
    def validate_operation(cls, v):
        valid_ops = ['discover', 'get_full_file', 'get_single_item', 'search_metadata', 'search_content']
        if v not in valid_ops:
            raise ValueError(f"Operation must be one of: {valid_ops}")
        return v

    @validator('search_type')
    def validate_search_type(cls, v):
        valid_types = ['exact', 'partial', 'regex']
        if v not in valid_types:
            raise ValueError(f"Search type must be one of: {valid_types}")
        return v


class JSONSearchTool(BaseTool):
    """
    LangChain tool for searching and fetching data from processed JSON documents.
    
    This tool searches through unified_results.json which contains processed data from:
    - PDF documents broken into searchable chunks
    - Excel spreadsheets with individual sheet data  
    - CSV files with structured data
    
    Available operations:
    1. discover - List all files in the dataset
    2. get_full_file - Get all content from a specific file
    3. get_single_item - Get specific page/sheet from a file
    4. search_metadata - Search in file metadata only
    5. search_content - Search in actual document text
    """
    
    name: str = "json_search_tool"
    description: str = """
    Search and fetch data from processed document JSON files (PDF, Excel, CSV).
    
    Operations:
    - discover: List all available files
    - get_full_file: Get complete content from a filename  
    - get_single_item: Get specific page/sheet (requires filename + page/sheet)
    - search_metadata: Search metadata fields (requires search_value, optional field)
    - search_content: Search document text (requires search_value)
    
    Examples:
    - {"operation": "discover"} - List all files
    - {"operation": "get_full_file", "filename": "document.pdf"} - Get all PDF content
    - {"operation": "get_single_item", "filename": "doc.pdf", "page": 5} - Get page 5
    - {"operation": "search_content", "search_value": "capital requirements"} - Find text
    - {"operation": "search_metadata", "search_value": "2025-08-06", "field": "processing_timestamp", "search_type": "partial"} - Search dates
    """
    args_schema: Type[BaseModel] = JSONSearchInput

    def _run(self, **kwargs) -> str:
        """Execute the JSON search operation with comprehensive error handling."""
        
        try:
            # Parse input
            inputs = JSONSearchInput(**kwargs)
            
            # Validate file path
            json_path = Path(inputs.json_file_path)
            if not json_path.exists():
                # Try relative to current directory
                alt_path = Path.cwd() / inputs.json_file_path
                if alt_path.exists():
                    json_path = alt_path
                else:
                    return self._format_error(
                        "FileNotFound",
                        f"JSON file not found: {inputs.json_file_path}",
                        f"Checked paths: {inputs.json_file_path}, {alt_path}",
                        "Ensure the JSON file exists and the path is correct"
                    )
            
            # Execute the requested operation
            return self._execute_operation(str(json_path), inputs)
            
        except Exception as e:
            return self._format_error(
                "UnexpectedError",
                str(e),
                f"Operation: {kwargs.get('operation', 'unknown')}",
                "Check input parameters and try again"
            )

    def _execute_operation(self, json_path: str, inputs: JSONSearchInput) -> str:
        """Execute the specific search operation."""
        
        try:
            if inputs.operation == "discover":
                result = discover_files(json_path)
                return self._format_success("File Discovery", result, inputs)
                
            elif inputs.operation == "get_full_file":
                if not inputs.filename:
                    return self._format_error(
                        "MissingParameter", 
                        "filename is required for get_full_file operation",
                        "Example: {'operation': 'get_full_file', 'filename': 'document.pdf'}",
                        "Provide a valid filename"
                    )
                
                result = get_full_file(json_path, inputs.filename)
                return self._format_success("Full File Results", result, inputs)
                
            elif inputs.operation == "get_single_item":
                if not inputs.filename:
                    return self._format_error(
                        "MissingParameter",
                        "filename is required for get_single_item operation", 
                        "Example: {'operation': 'get_single_item', 'filename': 'doc.pdf', 'page': 5}",
                        "Provide filename and page/sheet/chunk"
                    )
                
                if inputs.page is None and inputs.sheet is None:
                    return self._format_error(
                        "MissingParameter",
                        "Either page, sheet, or chunk must be specified for get_single_item",
                        "Examples: page=5 for PDFs, sheet='Balance Sheet' for Excel",
                        "Specify the target location within the file"
                    )
                
                result = get_single_item(
                    json_path, 
                    inputs.filename, 
                    page=inputs.page,
                    sheet=inputs.sheet, 
                    chunk=inputs.chunk
                )
                return self._format_success("Single Item Results", result, inputs)
                
            elif inputs.operation == "search_metadata":
                if inputs.search_value is None:
                    return self._format_error(
                        "MissingParameter",
                        "search_value is required for search_metadata operation",
                        "Example: {'operation': 'search_metadata', 'search_value': 'document.pdf', 'field': 'source_file'}",
                        "Provide a value to search for in metadata"
                    )
                
                result = search_metadata(
                    json_path,
                    inputs.search_value,
                    field=inputs.field,
                    search_type=inputs.search_type
                )
                return self._format_success("Metadata Search Results", result, inputs)
                
            elif inputs.operation == "search_content":
                if inputs.search_value is None:
                    return self._format_error(
                        "MissingParameter", 
                        "search_value is required for search_content operation",
                        "Example: {'operation': 'search_content', 'search_value': 'capital requirements'}",
                        "Provide text to search for in document content"
                    )
                
                result = search_content(
                    json_path,
                    str(inputs.search_value),
                    search_type=inputs.search_type
                )
                return self._format_success("Content Search Results", result, inputs)
                
            else:
                return self._format_error(
                    "InvalidOperation",
                    f"Unknown operation: {inputs.operation}",
                    "Valid operations: discover, get_full_file, get_single_item, search_metadata, search_content",
                    "Use one of the supported operations"
                )
                
        except FileNotFoundError as e:
            return self._format_error(
                "FileNotFound",
                str(e),
                f"File path: {json_path}",
                "Check that the JSON file exists and is accessible"
            )
        except json.JSONDecodeError as e:
            return self._format_error(
                "InvalidJSON",
                f"JSON parsing error: {e}",
                f"File: {json_path}",
                "Ensure the JSON file is valid and properly formatted"
            )
        except Exception as e:
            return self._format_error(
                "OperationError",
                str(e),
                f"Operation: {inputs.operation}",
                "Check your input parameters and try again"
            )

    def _format_success(self, operation_name: str, result: Dict[str, Any], inputs: JSONSearchInput) -> str:
        """Format successful operation results."""
        
        # Create a summary for easier consumption
        summary = {
            "operation": operation_name,
            "status": "SUCCESS",
            "input_parameters": {
                "operation": inputs.operation,
                "json_file_path": inputs.json_file_path,
                "filename": inputs.filename,
                "search_value": inputs.search_value,
                "field": inputs.field,
                "search_type": inputs.search_type,
                "page": inputs.page,
                "sheet": inputs.sheet,
                "chunk": inputs.chunk
            }
        }
        
        # Add operation-specific summary info
        if inputs.operation == "discover":
            summary["summary"] = f"Found {result.get('total_files', 0)} files"
            summary["files"] = result.get('files', [])
            
        elif inputs.operation == "get_full_file":
            summary["summary"] = f"Retrieved {result.get('total_items', 0)} items from {inputs.filename}"
            
        elif inputs.operation == "get_single_item":
            if result.get('status') == 'success':
                summary["summary"] = f"Found item in {inputs.filename}"
            else:
                summary["summary"] = f"Item not found in {inputs.filename}"
                
        elif inputs.operation in ["search_metadata", "search_content"]:
            summary["summary"] = f"Found {result.get('total_results', 0)} matches for '{inputs.search_value}'"
        
        # Combine summary and full results
        output = {
            "summary": summary,
            "detailed_results": result
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)

    def _format_error(self, error_type: str, message: str, details: str, suggestion: str) -> str:
        """Format error responses with detailed feedback."""
        
        error_response = {
            "status": "ERROR",
            "error_type": error_type,
            "message": message,
            "details": details,
            "suggestion": suggestion,
            "available_operations": [
                "discover - List all files",
                "get_full_file - Get complete file content", 
                "get_single_item - Get specific page/sheet",
                "search_metadata - Search file metadata",
                "search_content - Search document text"
            ],
            "example_usage": {
                "discover_files": {
                    "operation": "discover"
                },
                "get_pdf_content": {
                    "operation": "get_full_file",
                    "filename": "document.pdf"
                },
                "get_specific_page": {
                    "operation": "get_single_item", 
                    "filename": "document.pdf",
                    "page": 5
                },
                "search_text": {
                    "operation": "search_content",
                    "search_value": "capital requirements"
                },
                "search_metadata": {
                    "operation": "search_metadata",
                    "search_value": "2025-08-06",
                    "field": "processing_timestamp",
                    "search_type": "partial"
                }
            }
        }
        
        return json.dumps(error_response, indent=2, ensure_ascii=False)

    async def _arun(self, **kwargs) -> str:
        """Async version of _run."""
        return self._run(**kwargs)


def create_json_search_tool(json_file_path: str = "../Fetch_data/unified_results.json") -> JSONSearchTool:
    """
    Factory function to create a JSONSearchTool with a specific JSON file path.
    
    Args:
        json_file_path: Path to the unified_results.json file
        
    Returns:
        Configured JSONSearchTool instance
    """
    tool = JSONSearchTool()
    # Set default json file path
    tool.description = tool.description.replace(
        "Fetch_data/unified_results.json", 
        json_file_path
    )
    return tool


if __name__ == "__main__":
    """Example usage and testing."""
    
    # Create the tool
    tool = create_json_search_tool()
    
    print("🔍 LangChain JSON Search Tool Demo")
    print("=" * 50)
    
    # Test 1: Discover files
    print("\n1. Testing File Discovery:")
    result1 = tool._run(operation="discover")
    print(result1)
    
    # Test 2: Search content
    print("\n2. Testing Content Search:")
    result2 = tool._run(
        operation="search_content", 
        search_value="OSFI",
        search_type="partial"
    )
    print(result2)
    
    # Test 3: Error handling
    print("\n3. Testing Error Handling:")
    result3 = tool._run(operation="invalid_operation")
    print(result3)
    
    print("\n✅ Demo complete!")