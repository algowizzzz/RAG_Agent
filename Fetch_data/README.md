# JSON Search Tool - Developer Documentation

## 🎯 Overview

This tool helps you search through document data (PDFs, Excel, CSV) that has been processed into a unified JSON format. It provides 5 core functions to find and retrieve specific content from your document collection.

## 📋 What This Tool Does

The tool searches through `unified_results.json` which contains processed data from:
- **PDF documents** broken into searchable chunks
- **Excel spreadsheets** with individual sheet data  
- **CSV files** with structured data

Your current dataset contains:
- **3 files total**: 1 PDF (10,288 words), 1 Excel (150 words), 1 CSV (67 words)
- **52 searchable chunks** from the PDF document
- **40+ content matches** available for text searches

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or higher
- Your `unified_results.json` file in the same directory

### Basic Setup
```python
# Import all functions
from json_searcher import *

# Your data file (must be in same directory)
json_file = "unified_results.json"
```

## 📚 5 Core Functions

### 1️⃣ File Discovery - `discover_files()`
**Purpose**: List all files in your dataset

```python
# Get all available files
files = discover_files("unified_results.json")

print(f"Found {files['total_files']} files:")
for detail in files['details']:
    print(f"📁 {detail['filename']} ({detail['file_type']}) - {detail['words']} words")
```

**Output Example**:
```
Found 3 files:
📁 car24_chpt1_0.pdf (pdf) - 10288 words
📁 TechTrend_Financials_2024.xlsx (xlsx) - 150 words  
📁 test_business_data.csv (csv) - 67 words
```

**When to use**: Start here to see what files are available to search.

---

### 2️⃣ Full File Results - `get_full_file()`
**Purpose**: Get ALL content from a specific file

```python
# Get all chunks from a PDF file
pdf_content = get_full_file("unified_results.json", "car24_chpt1_0.pdf")

print(f"Retrieved {pdf_content['total_items']} chunks")
for item in pdf_content['items'][:3]:  # Show first 3
    print(f"Page {item['page']}, Chunk {item['chunk']}: {item['words']} words")

# Get all sheets from an Excel file
excel_content = get_full_file("unified_results.json", "TechTrend_Financials_2024.xlsx")

print(f"Retrieved {excel_content['total_items']} sheets:")
for item in excel_content['items']:
    print(f"📊 {item['sheet']}: {item['words']} words")
```

**Output Example**:
```
Retrieved 52 chunks
Page 0, Chunk 0: 346 words
Page 1, Chunk 1: 132 words
Page 2, Chunk 2: 178 words

Retrieved 3 sheets:
📊 Income Statement: 32 words
📊 Balance Sheet: 51 words
📊 Cash Flow Statement: 67 words
```

**When to use**: When you need complete content from a specific file.

---

### 3️⃣ Single Results - `get_single_item()`
**Purpose**: Get specific page/sheet from a file

```python
# Get specific PDF page
page_content = get_single_item("unified_results.json", "car24_chpt1_0.pdf", page=5)

if page_content['status'] == 'success':
    print(f"Page {page_content['page']}: {page_content['words']} words")
    print(f"Preview: {page_content['content'][:100]}...")

# Get specific Excel sheet
sheet_content = get_single_item("unified_results.json", 
                               "TechTrend_Financials_2024.xlsx", 
                               sheet="Balance Sheet")

if sheet_content['status'] == 'success':
    print(f"Sheet: {sheet_content['sheet']} ({sheet_content['words']} words)")
```

**Output Example**:
```
Page 5: 486 words
Preview: Banks/BHC/T&L Overview of risk-based capital requirements October 2023 Chapter 1 - Page 6...

Sheet: Balance Sheet (51 words)
```

**When to use**: When you need specific content from a known location.

---

### 4️⃣ Search Metadata - `search_metadata()`
**Purpose**: Search in file information (NOT document content)

```python
# Search by filename
filename_results = search_metadata("unified_results.json", 
                                 "car24_chpt1_0.pdf", 
                                 field="source_file")
print(f"Found {filename_results['total_results']} items with that filename")

# Search by page number
page_results = search_metadata("unified_results.json", 
                              10, 
                              field="page_number")
print(f"Found {page_results['total_results']} items from page 10")

# Search by processing date (partial match)
date_results = search_metadata("unified_results.json", 
                              "2025-08-06", 
                              search_type="partial")
print(f"Found {date_results['total_results']} items processed on 2025-08-06")
```

**Available metadata fields**:
- `source_file` - filename
- `page_number` - PDF page number
- `chunk_index` - chunk position
- `processing_timestamp` - when processed
- `chunk_hash` - unique identifier

**Search types**:
- `"exact"` - exact match (default)
- `"partial"` - contains substring
- `"regex"` - regular expression pattern

**When to use**: To find content by file properties, page numbers, or processing information.

---

### 5️⃣ Search Content - `search_content()`
**Purpose**: Search in actual document text

```python
# Search for specific text
capital_results = search_content("unified_results.json", "capital requirements")

print(f"Found {capital_results['total_results']} content matches")
if capital_results['results']:
    sample = capital_results['results'][0]
    print(f"📄 Found in: {sample['filename']}, Page {sample['page']}")
    print(f"💬 Context: {sample['match_preview']}")

# Search for organization name
osfi_results = search_content("unified_results.json", "OSFI")
print(f"Found {osfi_results['total_results']} mentions of 'OSFI'")

# Use regex for flexible patterns
regex_results = search_content("unified_results.json", 
                              "balance.*sheet", 
                              search_type="regex")
print(f"Found {regex_results['total_results']} regex matches")
```

**Output Example**:
```
Found 52 content matches
📄 Found in: car24_chpt1_0.pdf, Page 0
💬 Context: ...Banks/BHC/T&L Overview of risk-based capital requirements October 2023...

Found 40 mentions of 'OSFI'
Found 4 regex matches
```

**When to use**: To find specific words, phrases, or concepts in document content.

## 🛠️ Common Use Cases

### Finding Specific Document Sections
```python
# Find page 5 of a regulatory document
content = get_single_item("unified_results.json", "car24_chpt1_0.pdf", page=5)
print(content['content'])  # Full page content
```

### Searching for Keywords Across All Documents
```python
# Find all mentions of "capital requirements"
results = search_content("unified_results.json", "capital requirements")
for result in results['results'][:5]:  # Show first 5 matches
    print(f"📄 {result['filename']}, Page {result['page']}")
    print(f"   {result['match_preview']}")
```

### Getting Financial Data from Excel
```python
# Get balance sheet data
balance_sheet = get_single_item("unified_results.json", 
                               "TechTrend_Financials_2024.xlsx", 
                               sheet="Balance Sheet")
print(balance_sheet['content'])  # Excel data
```

### Finding All Content from a Specific File
```python
# Get everything from the PDF
all_pdf = get_full_file("unified_results.json", "car24_chpt1_0.pdf")
for chunk in all_pdf['items']:
    print(f"Page {chunk['page']}: {chunk['words']} words")
```

## 📊 Understanding Your Data

### File Breakdown
```
📁 car24_chpt1_0.pdf
   └── 26 pages → 52 searchable chunks → 10,288 total words

📁 TechTrend_Financials_2024.xlsx  
   ├── Income Statement (32 words)
   ├── Balance Sheet (51 words)
   └── Cash Flow Statement (67 words)

📁 test_business_data.csv
   └── Business data (67 words)
```

### Search Capabilities
- **52 chunks** available for content search
- **40+ content matches** for common terms like "OSFI"
- **3 file types** supported (PDF, Excel, CSV)
- **Multiple search types** (exact, partial, regex)

## ⚠️ Important Notes

### Response Structure
All functions return dictionaries with:
- `status` - "success" or "not_found"
- `results` or specific data fields
- Counts and metadata

### Error Handling
```python
result = get_single_item("unified_results.json", "nonexistent.pdf", page=1)
if result['status'] == 'not_found':
    print(result['message'])
```

### Performance Tips
- Use `search_metadata()` for faster searches when you know the field
- Use `get_single_item()` instead of `get_full_file()` when you need specific content
- Metadata searches are faster than content searches

## 🔧 Troubleshooting

### Common Issues

**Q: No results found**
```python
# Check if file exists first
files = discover_files("unified_results.json")
print(files['files'])  # See available files
```

**Q: Wrong file format**
```python
# Make sure your JSON file is in the same directory
import os
print(os.path.exists("unified_results.json"))  # Should return True
```

**Q: Empty content**
```python
# Check if the search found anything
results = search_content("unified_results.json", "your_term")
if results['total_results'] == 0:
    print("No matches found. Try a different search term.")
```

## 📝 Complete Example Script

```python
#!/usr/bin/env python3
"""
Example script showing all 5 functions
"""

from json_searcher import *

def main():
    json_file = "unified_results.json"
    
    # 1. Discover what files are available
    print("=== Available Files ===")
    files = discover_files(json_file)
    for detail in files['details']:
        print(f"📁 {detail['filename']} - {detail['words']} words")
    
    # 2. Get all content from PDF
    print("\n=== Full PDF Content ===")
    pdf_content = get_full_file(json_file, "car24_chpt1_0.pdf")
    print(f"Total chunks: {pdf_content['total_items']}")
    
    # 3. Get specific page
    print("\n=== Specific Page ===")
    page5 = get_single_item(json_file, "car24_chpt1_0.pdf", page=5)
    if page5['status'] == 'success':
        print(f"Page 5: {page5['words']} words")
    
    # 4. Search metadata
    print("\n=== Metadata Search ===")
    meta_results = search_metadata(json_file, "car24_chpt1_0.pdf", field="source_file")
    print(f"Items with that filename: {meta_results['total_results']}")
    
    # 5. Search content
    print("\n=== Content Search ===")
    content_results = search_content(json_file, "OSFI")
    print(f"Mentions of 'OSFI': {content_results['total_results']}")

if __name__ == "__main__":
    main()
```

## 🎓 Next Steps

1. **Start with file discovery** to see what's available
2. **Use single results** for targeted content retrieval
3. **Use content search** to find specific information
4. **Combine functions** for complex analysis workflows

Remember: This tool searches processed document data, not the original files. All content has been pre-processed and indexed for fast searching.