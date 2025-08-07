#!/usr/bin/env python3
"""
Clean Examples - 5 Core JSON Search Features
=============================================

Working examples for each of the 5 core features.
"""

from json_searcher import *

def demo_all_features():
    """Demonstrate all 5 core features with working examples."""
    
    json_file = "unified_results.json"
    
    print("🎯 JSON SEARCH TOOL - 5 Core Features")
    print("=" * 50)
    
    # 1. FILE DISCOVERY
    print("\n1️⃣  FILE DISCOVERY")
    print("📋 List all files in the dataset")
    files = discover_files(json_file)
    print(f"✅ Found {files['total_files']} files:")
    for detail in files['details']:
        print(f"   📁 {detail['filename']} ({detail['file_type']}) - {detail['words']} words")
    
    # 2. FULL FILE RESULTS  
    print("\n\n2️⃣  FULL FILE RESULTS")
    print("📄 Get ALL chunks from a PDF file")
    pdf_file = "car24_chpt1_0.pdf"
    full_pdf = get_full_file(json_file, pdf_file)
    print(f"✅ Retrieved {full_pdf['total_items']} chunks from {pdf_file}")
    print("   Sample chunks:")
    for item in full_pdf['items'][:3]:
        print(f"   • Page {item['page']}, Chunk {item['chunk']}: {item['words']} words")
    
    print("\n📊 Get ALL sheets from Excel file")
    excel_file = "TechTrend_Financials_2024.xlsx"
    full_excel = get_full_file(json_file, excel_file)
    print(f"✅ Retrieved {full_excel['total_items']} sheets from {excel_file}")
    for item in full_excel['items']:
        print(f"   • {item['sheet']}: {item['words']} words")
    
    # 3. SINGLE RESULTS
    print("\n\n3️⃣  SINGLE RESULTS")
    print("🎯 Get specific page from PDF")
    single_pdf = get_single_item(json_file, pdf_file, page=5)
    if single_pdf['status'] == 'success':
        print(f"✅ Page {single_pdf['page']}: {single_pdf['words']} words")
        print(f"   Preview: {single_pdf['content'][:80]}...")
    
    print("\n🎯 Get specific Excel sheet")
    single_excel = get_single_item(json_file, excel_file, sheet="Balance Sheet")
    if single_excel['status'] == 'success':
        print(f"✅ {single_excel['sheet']}: {single_excel['words']} words")
    
    # 4. SEARCH METADATA
    print("\n\n4️⃣  SEARCH METADATA")
    print("🔍 Search by filename")
    meta_filename = search_metadata(json_file, "car24_chpt1_0.pdf", field="source_file")
    print(f"✅ Found {meta_filename['total_results']} items with filename 'car24_chpt1_0.pdf'")
    
    print("\n🔍 Search by page number")
    meta_page = search_metadata(json_file, 10, field="page_number")
    print(f"✅ Found {meta_page['total_results']} items from page 10")
    
    print("\n🔍 Search by processing date")
    meta_date = search_metadata(json_file, "2025-08-06", search_type="partial")
    print(f"✅ Found {meta_date['total_results']} items processed on 2025-08-06")
    
    # 5. SEARCH ACTUAL CONTENT
    print("\n\n5️⃣  SEARCH ACTUAL CONTENT")
    print("📝 Search for 'capital requirements' in document text")
    content_capital = search_content(json_file, "capital requirements")
    print(f"✅ Found {content_capital['total_results']} content matches")
    if content_capital['results']:
        sample = content_capital['results'][0]
        print(f"   📄 Sample: {sample['filename']}, Page {sample['page']}")
        print(f"   💬 Match: {sample['match_preview'][:60]}...")
    
    print("\n📝 Search for 'OSFI' in document text")
    content_osfi = search_content(json_file, "OSFI")
    print(f"✅ Found {content_osfi['total_results']} content matches for 'OSFI'")
    
    print("\n📝 Regex search for 'balance.*sheet'")
    content_regex = search_content(json_file, "balance.*sheet", search_type="regex")
    print(f"✅ Found {content_regex['total_results']} regex matches")
    
    print("\n🎉 All 5 core features demonstrated!")


def quick_reference():
    """Show quick reference for all functions."""
    
    print("\n\n📚 QUICK REFERENCE")
    print("=" * 50)
    
    functions = [
        ("discover_files(file)", "List all files in dataset"),
        ("get_full_file(file, filename)", "Get ALL chunks/sheets from file"),
        ("get_single_item(file, filename, page=X)", "Get specific PDF page"),
        ("get_single_item(file, filename, sheet='Name')", "Get specific Excel sheet"),
        ("search_metadata(file, value, field='name')", "Search metadata fields only"),
        ("search_content(file, 'text')", "Search actual document content")
    ]
    
    for func, desc in functions:
        print(f"🔧 {func:<45} # {desc}")
    
    print(f"\n📊 Your Data:")
    files = discover_files("unified_results.json")
    for detail in files['details']:
        print(f"   📁 {detail['filename']} - {detail['words']} words")


if __name__ == "__main__":
    demo_all_features()
    quick_reference()