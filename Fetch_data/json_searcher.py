#!/usr/bin/env python3
"""
Clean JSON Search Tool - 5 Core Features
=========================================

1. File discovery - List all files
2. Full file results - All chunks/sheets by filename  
3. Single results - Specific page/chunk/sheet + filename
4. Search metadata - Search metadata fields only
5. Search actual content - Search document text content

Author: AI Assistant
Date: 2025-08-06
"""

import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


class JSONSearcher:
    """Clean JSON searcher with 5 core features."""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = Path(json_file_path)
        self.data = self._load_json()
        
    def _load_json(self) -> Dict[str, Any]:
        """Load and parse the JSON file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")


# 1. FILE DISCOVERY - List all files
def discover_files(json_file_path: str) -> Dict[str, Any]:
    """
    Discover all files in the dataset.
    
    Returns all filenames with basic info.
    """
    searcher = JSONSearcher(json_file_path)
    filenames = set()
    file_details = []
    
    # Get from metadata
    if "metadata" in searcher.data and "file_breakdown" in searcher.data["metadata"]:
        for file_info in searcher.data["metadata"]["file_breakdown"]:
            if "filename" in file_info:
                filename = file_info["filename"]
                filenames.add(filename)
                file_details.append({
                    "filename": filename,
                    "file_type": file_info.get("file_type", "unknown"),
                    "chunks": file_info.get("chunks", "N/A"),
                    "words": file_info.get("words", "N/A"),
                    "sheets": file_info.get("sheets", "N/A")
                })
    
    return {
        "status": "success",
        "total_files": len(filenames),
        "files": sorted(list(filenames)),
        "details": file_details
    }


# 2. FULL FILE RESULTS - All chunks/sheets by filename
def get_full_file(json_file_path: str, filename: str) -> Dict[str, Any]:
    """
    Get ALL chunks/sheets from a specific file.
    
    Returns complete file content (all chunks for PDF, all sheets for Excel).
    """
    searcher = JSONSearcher(json_file_path)
    results = []
    
    # Search PDF chunks
    if "pdf_results" in searcher.data:
        for chunk in searcher.data["pdf_results"].get("chunks", []):
            if chunk.get("metadata", {}).get("source_file") == filename:
                results.append({
                    "type": "pdf_chunk",
                    "page": chunk["metadata"]["page_number"],
                    "chunk": chunk["metadata"]["chunk_index"],
                    "words": chunk["statistics"]["word_count"],
                    "content": chunk["content"]
                })
    
    # Search Excel/CSV data
    if "unified_data" in searcher.data:
        for item in searcher.data["unified_data"]:
            if item.get("source_file") == filename:
                results.append({
                    "type": item.get("type", "unknown"),
                    "sheet": item.get("source_sheet", "N/A"),
                    "words": item.get("word_count", 0),
                    "content": item.get("content", {})
                })
    
    return {
        "status": "success",
        "filename": filename,
        "total_items": len(results),
        "items": results
    }


# 3. SINGLE RESULTS - Specific page/chunk/sheet + filename
def get_single_item(json_file_path: str, filename: str, page: Optional[int] = None, 
                   sheet: Optional[str] = None, chunk: Optional[int] = None) -> Dict[str, Any]:
    """
    Get specific single item by filename + page/sheet/chunk.
    
    Examples:
    - get_single_item(file, "doc.pdf", page=5)
    - get_single_item(file, "data.xlsx", sheet="Balance Sheet")
    - get_single_item(file, "doc.pdf", page=5, chunk=0)
    """
    searcher = JSONSearcher(json_file_path)
    
    # Search PDF chunks
    if page is not None and "pdf_results" in searcher.data:
        for chunk_data in searcher.data["pdf_results"].get("chunks", []):
            meta = chunk_data.get("metadata", {})
            if (meta.get("source_file") == filename and 
                meta.get("page_number") == page and
                (chunk is None or meta.get("chunk_index") == chunk)):
                
                return {
                    "status": "success",
                    "type": "pdf_chunk",
                    "filename": filename,
                    "page": meta["page_number"],
                    "chunk": meta["chunk_index"],
                    "words": chunk_data["statistics"]["word_count"],
                    "content": chunk_data["content"]
                }
    
    # Search Excel/CSV by sheet
    if sheet is not None and "unified_data" in searcher.data:
        for item in searcher.data["unified_data"]:
            if (item.get("source_file") == filename and 
                item.get("source_sheet") == sheet):
                
                return {
                    "status": "success",
                    "type": item.get("type", "unknown"),
                    "filename": filename,
                    "sheet": item["source_sheet"],
                    "words": item.get("word_count", 0),
                    "content": item.get("content", {})
                }
    
    return {
        "status": "not_found",
        "message": f"No item found for {filename} with specified criteria"
    }


# 4. SEARCH METADATA - Search metadata fields only
def search_metadata(json_file_path: str, search_value: Any, field: Optional[str] = None, 
                   search_type: str = "exact") -> Dict[str, Any]:
    """
    Search ONLY in metadata fields.
    
    Examples:
    - search_metadata(file, "car24_chpt1_0.pdf", "source_file")
    - search_metadata(file, "2025-08-06", "processing_timestamp", "partial")
    - search_metadata(file, 5, "page_number")
    """
    searcher = JSONSearcher(json_file_path)
    results = []
    
    def value_matches(value, search_val, search_type):
        val_str = str(value).lower()
        search_str = str(search_val).lower()
        if search_type == "exact":
            return val_str == search_str
        elif search_type == "partial":
            return search_str in val_str
        elif search_type == "regex":
            return bool(re.search(search_str, val_str))
        return False
    
    # Search PDF metadata
    if "pdf_results" in searcher.data:
        for chunk in searcher.data["pdf_results"].get("chunks", []):
            metadata = chunk.get("metadata", {})
            matched = False
            
            if field and field in metadata:
                matched = value_matches(metadata[field], search_value, search_type)
            elif not field:
                matched = any(value_matches(v, search_value, search_type) for v in metadata.values())
            
            if matched:
                results.append({
                    "type": "pdf_chunk",
                    "metadata": metadata,
                    "content_preview": chunk["content"][:100] + "..."
                })
    
    # Search unified data metadata
    if "unified_data" in searcher.data:
        for item in searcher.data["unified_data"]:
            metadata = item.get("metadata", {})
            item_fields = {k: v for k, v in item.items() if k != "content"}
            all_fields = {**metadata, **item_fields}
            matched = False
            
            if field and field in all_fields:
                matched = value_matches(all_fields[field], search_value, search_type)
            elif not field:
                matched = any(value_matches(v, search_value, search_type) for v in all_fields.values())
            
            if matched:
                results.append({
                    "type": item.get("type", "unknown"),
                    "metadata": all_fields,
                    "content_preview": str(item.get("content", ""))[:100] + "..."
                })
    
    return {
        "status": "success",
        "search_value": search_value,
        "field": field,
        "search_type": search_type,
        "total_results": len(results),
        "results": results
    }


# 5. SEARCH ACTUAL CONTENT - Search document text content
def search_content(json_file_path: str, search_value: str, search_type: str = "partial") -> Dict[str, Any]:
    """
    Search ACTUAL document content text.
    
    Examples:
    - search_content(file, "capital requirements")
    - search_content(file, "Balance.*Sheet", "regex")
    - search_content(file, "OSFI")
    """
    searcher = JSONSearcher(json_file_path)
    results = []
    
    def content_matches(content, search_val, search_type):
        content_str = str(content).lower()
        search_str = str(search_val).lower()
        if search_type == "exact":
            return search_str == content_str
        elif search_type == "partial":
            return search_str in content_str
        elif search_type == "regex":
            return bool(re.search(search_str, content_str))
        return False
    
    # Search PDF content
    if "pdf_results" in searcher.data:
        for chunk in searcher.data["pdf_results"].get("chunks", []):
            content = chunk.get("content", "")
            if content_matches(content, search_value, search_type):
                meta = chunk["metadata"]
                # Find position of match for preview
                match_pos = content.lower().find(str(search_value).lower())
                start = max(0, match_pos - 50)
                end = min(len(content), match_pos + len(str(search_value)) + 50)
                preview = content[start:end]
                
                results.append({
                    "type": "pdf_chunk",
                    "filename": meta["source_file"],
                    "page": meta["page_number"],
                    "chunk": meta["chunk_index"],
                    "match_preview": f"...{preview}...",
                    "word_count": chunk["statistics"]["word_count"]
                })
    
    # Search unified data content
    if "unified_data" in searcher.data:
        for item in searcher.data["unified_data"]:
            content = str(item.get("content", ""))
            if content_matches(content, search_value, search_type):
                match_pos = content.lower().find(str(search_value).lower())
                start = max(0, match_pos - 50)
                end = min(len(content), match_pos + len(str(search_value)) + 50)
                preview = content[start:end]
                
                results.append({
                    "type": item.get("type", "unknown"),
                    "filename": item.get("source_file", "unknown"),
                    "sheet": item.get("source_sheet", "N/A"),
                    "match_preview": f"...{preview}...",
                    "word_count": item.get("word_count", 0)
                })
    
    return {
        "status": "success",
        "search_value": search_value,
        "search_type": search_type,
        "total_results": len(results),
        "results": results
    }


if __name__ == "__main__":
    # Simple examples
    import sys
    
    if len(sys.argv) < 2:
        print("Usage examples:")
        print("python json_searcher_clean.py unified_results.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    print("🔍 JSON Search Tool - 5 Core Features Demo")
    print("=" * 50)
    
    # 1. Discover files
    print("\n1. File Discovery:")
    files = discover_files(json_file)
    print(f"Found {files['total_files']} files: {files['files']}")
    
    # 2. Get full file (first PDF)
    if files['files']:
        pdf_file = next((f for f in files['files'] if 'pdf' in f), None)
        if pdf_file:
            print(f"\n2. Full File Results for {pdf_file}:")
            full_file = get_full_file(json_file, pdf_file)
            print(f"Total items: {full_file['total_items']}")
    
    # 3. Single item
    if pdf_file:
        print(f"\n3. Single Item - {pdf_file} page 5:")
        single = get_single_item(json_file, pdf_file, page=5)
        if single['status'] == 'success':
            print(f"Found: {single['words']} words")
    
    # 4. Search metadata
    print("\n4. Search Metadata for 'pdf':")
    meta_results = search_metadata(json_file, "pdf", search_type="partial")
    print(f"Found {meta_results['total_results']} metadata matches")
    
    # 5. Search content
    print("\n5. Search Content for 'risk':")
    content_results = search_content(json_file, "risk")
    print(f"Found {content_results['total_results']} content matches")