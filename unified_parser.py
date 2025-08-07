#!/usr/bin/env python3
"""
Unified Parser - Process PDF, Excel, and CSV files into one consolidated JSON
Automatically detects file types and routes to appropriate parsers.
"""

import os
import sys
import json
import argparse
import glob
from datetime import datetime
from typing import List, Dict, Any, Tuple
import hashlib

# Add parent directories to path to import existing parsers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'pdf_chunk_extractor_tool'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'excel_parser'))

class UnifiedParser:
    """Unified parser that combines PDF and Excel/CSV processing."""
    
    def __init__(self):
        """Initialize the unified parser."""
        self.supported_extensions = {
            'pdf': ['.pdf'],
            'excel': ['.xlsx', '.xls'],
            'csv': ['.csv']
        }
        
    def detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.supported_extensions['pdf']:
            return 'pdf'
        elif ext in self.supported_extensions['excel']:
            return 'excel'
        elif ext in self.supported_extensions['csv']:
            return 'csv'
        else:
            return 'unknown'
    
    def find_files(self, input_path: str) -> Dict[str, List[str]]:
        """Find and categorize files by type."""
        files = {
            'pdf': [],
            'excel': [],
            'csv': [],
            'unknown': []
        }
        
        if os.path.isfile(input_path):
            file_type = self.detect_file_type(input_path)
            if file_type == 'excel':
                files['excel'].append(input_path)
            elif file_type == 'csv':
                files['csv'].append(input_path)
            elif file_type == 'pdf':
                files['pdf'].append(input_path)
            else:
                files['unknown'].append(input_path)
        
        elif os.path.isdir(input_path):
            # Search for all supported file types
            all_extensions = (
                self.supported_extensions['pdf'] + 
                self.supported_extensions['excel'] + 
                self.supported_extensions['csv']
            )
            
            for ext in all_extensions:
                pattern = os.path.join(input_path, f"*{ext}")
                found_files = glob.glob(pattern)
                
                for file_path in found_files:
                    file_type = self.detect_file_type(file_path)
                    if file_type in files:
                        files[file_type].append(file_path)
        
        return files
    
    def process_pdf_files(self, pdf_files: List[str]) -> Dict[str, Any]:
        """Process PDF files using the PDF chunk extractor."""
        if not pdf_files:
            return {"metadata": {"total_files": 0}, "documents": [], "chunks": []}
        
        try:
            # Import PDF extractor
            from pdf_chunk_extractor import PDFChunkExtractor
            
            print(f"📄 Processing {len(pdf_files)} PDF files...")
            extractor = PDFChunkExtractor(chunk_size=5000, chunk_overlap=100)
            result = extractor.process_pdf_files(pdf_files)
            return result
            
        except ImportError as e:
            print(f"❌ Error importing PDF extractor: {e}")
            return {"error": "PDF extractor not available", "metadata": {"total_files": 0}, "documents": [], "chunks": []}
        except Exception as e:
            print(f"❌ Error processing PDF files: {e}")
            return {"error": str(e), "metadata": {"total_files": 0}, "documents": [], "chunks": []}
    
    def process_excel_csv_files(self, excel_files: List[str], csv_files: List[str]) -> Dict[str, Any]:
        """Process Excel and CSV files using the Excel parser."""
        all_files = excel_files + csv_files
        if not all_files:
            return {"metadata": {"total_files": 0}, "documents": [], "data": []}
        
        try:
            # Import Excel parser
            from excel_parser import EnhancedExcelCSVParser
            
            print(f"📊 Processing {len(all_files)} Excel/CSV files...")
            parser = EnhancedExcelCSVParser()
            result = parser.process_files(all_files)
            return result
            
        except ImportError as e:
            print(f"❌ Error importing Excel parser: {e}")
            return {"error": "Excel parser not available", "metadata": {"total_files": 0}, "documents": [], "data": []}
        except Exception as e:
            print(f"❌ Error processing Excel/CSV files: {e}")
            return {"error": str(e), "metadata": {"total_files": 0}, "documents": [], "data": []}
    
    def create_unified_metadata(self, pdf_result: Dict[str, Any], excel_result: Dict[str, Any], 
                               file_counts: Dict[str, int]) -> Dict[str, Any]:
        """Create unified metadata combining both tool results."""
        
        # Get safe metadata values
        pdf_meta = pdf_result.get("metadata", {})
        excel_meta = excel_result.get("metadata", {})
        
        pdf_words = pdf_meta.get("total_words", 0)
        excel_words = excel_meta.get("total_words", 0)
        
        # Create file breakdown
        file_breakdown = []
        
        # Add PDF files
        for doc in pdf_result.get("documents", []):
            file_breakdown.append({
                "filename": doc.get("filename", "unknown"),
                "file_type": "pdf",
                "sheets": "N/A",
                "chunks": doc.get("chunks_count", 0),
                "words": doc.get("total_words", 0)
            })
        
        # Add Excel/CSV files
        for doc in excel_result.get("documents", []):
            sheets = "N/A"
            if doc.get("word_count_by_sheet"):
                sheets = [sheet["sheet_name"] for sheet in doc["word_count_by_sheet"]]
            
            file_breakdown.append({
                "filename": doc.get("filename", "unknown"),
                "file_type": doc.get("file_type", "unknown"),
                "sheets": sheets,
                "chunks": "N/A",
                "words": doc.get("total_words", 0)
            })
        
        unified_metadata = {
            "processing_timestamp": datetime.now().isoformat(),
            "source_type": "unified_parser",
            "total_files": file_counts.get("pdf", 0) + file_counts.get("excel", 0) + file_counts.get("csv", 0),
            "total_words": pdf_words + excel_words,
            "pdf_files": file_counts.get("pdf", 0),
            "excel_files": file_counts.get("excel", 0),
            "csv_files": file_counts.get("csv", 0),
            "unknown_files": file_counts.get("unknown", 0),
            "file_breakdown": file_breakdown,
            "processing_summary": {
                "pdf_chunks": pdf_meta.get("total_chunks", 0),
                "excel_tables": excel_meta.get("total_tables", 0),
                "total_pages": pdf_meta.get("total_pages", 0),
                "total_sheets": excel_meta.get("total_sheets", 0)
            },
            "errors": []
        }
        
        # Add any errors
        if "error" in pdf_result:
            unified_metadata["errors"].append(f"PDF processing: {pdf_result['error']}")
        if "error" in excel_result:
            unified_metadata["errors"].append(f"Excel/CSV processing: {excel_result['error']}")
        
        return unified_metadata
    
    def create_unified_data(self, pdf_result: Dict[str, Any], excel_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create unified data array combining chunks and tables."""
        unified_data = []
        
        # Add PDF chunks
        for chunk in pdf_result.get("chunks", []):
            unified_item = {
                "id": chunk.get("global_chunk_id", f"pdf_chunk_{chunk.get('chunk_id', 'unknown')}"),
                "type": "pdf_chunk",
                "source_file": chunk.get("metadata", {}).get("source_file", "unknown"),
                "source_sheet": "N/A",
                "content": chunk.get("content", ""),
                "word_count": chunk.get("statistics", {}).get("word_count", 0),
                "metadata": {
                    "chunk_index": chunk.get("metadata", {}).get("chunk_index", 0),
                    "page_number": chunk.get("metadata", {}).get("page_number", "unknown"),
                    "chunk_size_chars": chunk.get("statistics", {}).get("character_count", 0)
                }
            }
            unified_data.append(unified_item)
        
        # Add Excel/CSV tables
        for table in excel_result.get("data", []):
            unified_item = {
                "id": table.get("global_table_id", f"table_{table.get('table_id', 'unknown')}"),
                "type": "excel_table" if table.get("metadata", {}).get("source_file", "").endswith(('.xlsx', '.xls')) else "csv_table",
                "source_file": table.get("metadata", {}).get("source_file", "unknown"),
                "source_sheet": table.get("metadata", {}).get("source_sheet", "unknown"),
                "content": table.get("content", {}),
                "word_count": table.get("statistics", {}).get("word_count", 0),
                "metadata": {
                    "table_id": table.get("table_id", 0),
                    "row_count": table.get("statistics", {}).get("row_count", 0),
                    "column_count": table.get("statistics", {}).get("column_count", 0),
                    "is_chunked": table.get("metadata", {}).get("is_chunked", False)
                }
            }
            unified_data.append(unified_item)
        
        return unified_data
    
    def process_files(self, input_path: str, output_file: str = "unified_output.json") -> Dict[str, Any]:
        """Main processing function."""
        print("🚀 Starting Unified File Processing...")
        print(f"📁 Input path: {input_path}")
        print(f"💾 Output file: {output_file}")
        print()
        
        # Find and categorize files
        files_by_type = self.find_files(input_path)
        
        # Count files
        file_counts = {ftype: len(flist) for ftype, flist in files_by_type.items()}
        total_files = sum(file_counts.values())
        
        print(f"📊 File Discovery Summary:")
        print(f"   📄 PDF files: {file_counts['pdf']}")
        print(f"   📊 Excel files: {file_counts['excel']}")
        print(f"   📝 CSV files: {file_counts['csv']}")
        print(f"   ❓ Unknown files: {file_counts['unknown']}")
        print(f"   📁 Total files: {total_files}")
        print()
        
        if file_counts['unknown'] > 0:
            print(f"⚠️  Skipping {file_counts['unknown']} unknown file(s): {files_by_type['unknown']}")
            print()
        
        if total_files - file_counts['unknown'] == 0:
            print("❌ No supported files found!")
            return {}
        
        # Process files by type
        pdf_result = self.process_pdf_files(files_by_type['pdf'])
        excel_result = self.process_excel_csv_files(files_by_type['excel'], files_by_type['csv'])
        
        # Create unified output
        unified_metadata = self.create_unified_metadata(pdf_result, excel_result, file_counts)
        unified_data = self.create_unified_data(pdf_result, excel_result)
        
        consolidated_result = {
            "metadata": unified_metadata,
            "pdf_results": pdf_result,
            "excel_results": excel_result,
            "unified_data": unified_data
        }
        
        # Save to JSON
        print(f"💾 Saving consolidated results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_result, f, indent=2, ensure_ascii=False, default=str)
        
        # Print summary
        print(f"✅ Processing completed successfully!")
        print(f"📊 Final Summary:")
        print(f"   📁 Total files processed: {unified_metadata['total_files']}")
        print(f"   💬 Total words: {unified_metadata['total_words']:,}")
        print(f"   📄 PDF chunks: {unified_metadata['processing_summary']['pdf_chunks']}")
        print(f"   📊 Excel tables: {unified_metadata['processing_summary']['excel_tables']}")
        print(f"   🔗 Unified data items: {len(unified_data)}")
        if unified_metadata['errors']:
            print(f"   ⚠️  Errors: {len(unified_metadata['errors'])}")
        print(f"   💾 Output: {output_file}")
        
        return consolidated_result

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Unified Parser - Process PDF, Excel, and CSV files into consolidated JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all files in combine folder
  python unified_parser.py combine/ --output unified_results.json
  
  # Process specific directory
  python unified_parser.py /path/to/files --output results.json
  
  # Process single file
  python unified_parser.py document.pdf --output single_result.json
        """
    )
    
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', default='unified_output.json',
                       help='Output JSON file (default: unified_output.json)')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        print(f"❌ Error: Input path '{args.input}' does not exist!")
        sys.exit(1)
    
    # Initialize and run parser
    try:
        unified_parser = UnifiedParser()
        result = unified_parser.process_files(args.input, args.output)
        
        if not result:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()