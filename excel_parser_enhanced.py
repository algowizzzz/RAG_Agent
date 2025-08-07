#!/usr/bin/env python3
"""
Enhanced Excel/CSV Parser Tool with Word Counting and Chunking
A standalone tool that processes Excel and CSV files into metadata-rich JSON format
with standardized structure compatible with the PDF chunk extractor.

Features:
- Word count by sheet
- Intelligent chunking for large tables
- Preserves data structure

Usage:
    python excel_parser_enhanced.py input_folder/ output_file.json
    python excel_parser_enhanced.py --files file1.xlsx file2.csv --output data.json
    python excel_parser_enhanced.py --help
"""

import os
import sys
import glob
import json
import argparse
import hashlib
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import required libraries
try:
    import pandas as pd
    import openpyxl  # Required for Excel reading
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install required packages:")
    print("pip install pandas openpyxl")
    sys.exit(1)

class EnhancedExcelCSVParser:
    """Enhanced Excel/CSV processor with word counting and chunking."""
    
    def __init__(self, preserve_dtypes: bool = True, include_empty_rows: bool = False, 
                 max_rows_per_chunk: int = 1000, max_size_mb: float = 10.0):
        """
        Initialize the enhanced Excel/CSV parser.
        
        Args:
            preserve_dtypes: Whether to preserve original data types (default: True)
            include_empty_rows: Whether to include completely empty rows (default: False)
            max_rows_per_chunk: Maximum rows per chunk when chunking (default: 1000)
            max_size_mb: Maximum size in MB before chunking (default: 10.0)
        """
        self.preserve_dtypes = preserve_dtypes
        self.include_empty_rows = include_empty_rows
        self.max_rows_per_chunk = max_rows_per_chunk
        self.max_size_mb = max_size_mb
    
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple Excel/CSV files into JSON format."""
        print(f"🔄 Processing {len(file_paths)} files...")
        
        # Initialize result structure
        result = {
            "metadata": {
                "processing_timestamp": datetime.now().isoformat(),
                "source_type": "excel_csv_enhanced",
                "preserve_dtypes": self.preserve_dtypes,
                "include_empty_rows": self.include_empty_rows,
                "chunking_settings": {
                    "max_rows_per_chunk": self.max_rows_per_chunk,
                    "max_size_mb": self.max_size_mb
                },
                "total_files": len(file_paths),
                "files_processed": [],
                "total_sheets": 0,
                "total_tables": 0,
                "total_rows": 0,
                "total_columns": 0,
                "total_words": 0,
                "word_count_by_sheet": []
            },
            "documents": [],
            "data": []
        }
        
        table_id = 0
        
        for file_path in file_paths:
            try:
                file_result = self._process_single_file(file_path, table_id)
                
                # Update metadata
                result["metadata"]["files_processed"].append({
                    "filename": os.path.basename(file_path),
                    "full_path": os.path.abspath(file_path),
                    "file_type": self._get_file_type(file_path),
                    "sheets": file_result["sheets_count"],
                    "tables": file_result["tables_count"],
                    "total_rows": file_result["total_rows"],
                    "total_columns": file_result["total_columns"],
                    "total_words": file_result["total_words"],
                    "word_count_by_sheet": file_result["word_count_by_sheet"],
                    "chunked_tables": file_result.get("chunked_tables", 0),
                    "file_size_bytes": os.path.getsize(file_path),
                    "file_hash": self._get_file_hash(file_path)
                })
                
                result["metadata"]["total_sheets"] += file_result["sheets_count"]
                result["metadata"]["total_tables"] += file_result["tables_count"]
                result["metadata"]["total_rows"] += file_result["total_rows"]
                result["metadata"]["total_columns"] += file_result["total_columns"]
                result["metadata"]["total_words"] += file_result["total_words"]
                result["metadata"]["word_count_by_sheet"].extend(file_result["word_count_by_sheet"])
                
                # Add document info
                result["documents"].append(file_result["document_info"])
                
                # Add table data
                result["data"].extend(file_result["tables"])
                
                # Update table counter
                table_id += file_result["tables_count"]
                
                print(f"✅ Processed {os.path.basename(file_path)}: {file_result['sheets_count']} sheets, {file_result['tables_count']} tables, {file_result['total_words']} words")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                result["metadata"]["files_processed"].append({
                    "filename": os.path.basename(file_path),
                    "full_path": os.path.abspath(file_path),
                    "error": str(e),
                    "status": "failed"
                })
        
        # Calculate summary statistics
        successful_files = [f for f in result["metadata"]["files_processed"] if "error" not in f]
        result["metadata"]["average_tables_per_file"] = (
            result["metadata"]["total_tables"] / len(successful_files)
            if successful_files else 0
        )
        result["metadata"]["average_words_per_sheet"] = (
            result["metadata"]["total_words"] / result["metadata"]["total_sheets"]
            if result["metadata"]["total_sheets"] > 0 else 0
        )
        
        print(f"🎯 Processing complete: {result['metadata']['total_tables']} tables, {result['metadata']['total_words']} words from {result['metadata']['total_sheets']} sheets")
        
        return result
    
    def _process_single_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process a single Excel or CSV file."""
        file_type = self._get_file_type(file_path)
        
        if file_type == "csv":
            return self._process_csv_file(file_path, start_table_id)
        elif file_type in ["xlsx", "xls"]:
            return self._process_excel_file(file_path, start_table_id)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _process_csv_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process a CSV file."""
        df = pd.read_csv(file_path)
        
        if not self.include_empty_rows:
            df = df.dropna(how='all')
        
        # Calculate word count
        word_count = self._count_words_in_dataframe(df)
        
        # Check if chunking is needed
        chunked_tables = 0
        tables = []
        
        if self._should_chunk_table(df):
            print(f"   📦 Chunking CSV file ({len(df)} rows)")
            df_chunks = self._chunk_large_table(df)
            chunked_tables = 1
            
            for chunk_index, df_chunk in enumerate(df_chunks):
                table_data = self._dataframe_to_nested_json(
                    df_chunk, file_path, "CSV_Data", start_table_id + chunk_index, 
                    chunk_index, len(df_chunks)
                )
                tables.append(table_data)
        else:
            table_data = self._dataframe_to_nested_json(df, file_path, "CSV_Data", start_table_id)
            tables.append(table_data)
        
        return {
            "document_info": {
                "filename": os.path.basename(file_path),
                "full_path": os.path.abspath(file_path),
                "file_type": "csv",
                "sheets_count": 1,
                "tables_count": len(tables),
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "total_words": word_count,
                "word_count_by_sheet": [{"sheet_name": "CSV_Data", "word_count": word_count}],
                "chunked_tables": chunked_tables,
                "file_size_bytes": os.path.getsize(file_path),
                "file_hash": self._get_file_hash(file_path),
                "processing_timestamp": datetime.now().isoformat()
            },
            "tables": tables,
            "sheets_count": 1,
            "tables_count": len(tables),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_words": word_count,
            "word_count_by_sheet": [{"sheet_name": "CSV_Data", "word_count": word_count}],
            "chunked_tables": chunked_tables
        }
    
    def _process_excel_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process an Excel file with multiple sheets."""
        sheet_dict = pd.read_excel(file_path, sheet_name=None)
        
        tables = []
        total_rows = 0
        total_columns = 0
        total_words = 0
        word_count_by_sheet = []
        chunked_tables = 0
        table_id = start_table_id
        
        for sheet_name, df in sheet_dict.items():
            if not self.include_empty_rows:
                df = df.dropna(how='all')
            
            if not df.empty:
                # Calculate word count for this sheet
                sheet_word_count = self._count_words_in_dataframe(df)
                word_count_by_sheet.append({"sheet_name": sheet_name, "word_count": sheet_word_count})
                total_words += sheet_word_count
                
                # Check if table should be chunked
                if self._should_chunk_table(df):
                    print(f"   📦 Chunking large sheet '{sheet_name}' ({len(df)} rows)")
                    df_chunks = self._chunk_large_table(df)
                    chunked_tables += 1
                    
                    for chunk_index, df_chunk in enumerate(df_chunks):
                        table_data = self._dataframe_to_nested_json(
                            df_chunk, file_path, sheet_name, table_id, 
                            chunk_index, len(df_chunks)
                        )
                        tables.append(table_data)
                        table_id += 1
                else:
                    table_data = self._dataframe_to_nested_json(df, file_path, sheet_name, table_id)
                    tables.append(table_data)
                    table_id += 1
                
                total_rows += len(df)
                total_columns += len(df.columns)
        
        return {
            "document_info": {
                "filename": os.path.basename(file_path),
                "full_path": os.path.abspath(file_path),
                "file_type": self._get_file_type(file_path),
                "sheets_count": len(sheet_dict),
                "tables_count": len(tables),
                "total_rows": total_rows,
                "total_columns": total_columns,
                "total_words": total_words,
                "word_count_by_sheet": word_count_by_sheet,
                "chunked_tables": chunked_tables,
                "file_size_bytes": os.path.getsize(file_path),
                "file_hash": self._get_file_hash(file_path),
                "processing_timestamp": datetime.now().isoformat(),
                "sheet_names": list(sheet_dict.keys())
            },
            "tables": tables,
            "sheets_count": len(sheet_dict),
            "tables_count": len(tables),
            "total_rows": total_rows,
            "total_columns": total_columns,
            "total_words": total_words,
            "word_count_by_sheet": word_count_by_sheet,
            "chunked_tables": chunked_tables
        }
    
    def _dataframe_to_nested_json(self, df: pd.DataFrame, file_path: str, sheet_name: str, table_id: int, 
                                  chunk_index: int = 0, total_chunks: int = 1) -> Dict[str, Any]:
        """Convert DataFrame to nested JSON structure preserving Excel layout."""
        
        # Convert DataFrame to nested JSON (preserving Excel structure)
        if self.preserve_dtypes:
            table_content = {
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),  # List of row dictionaries - preserves structure
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "shape": list(df.shape)
            }
        else:
            table_content = {
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "shape": list(df.shape)
            }
        
        # Create chunk identifier
        chunk_suffix = f"_chunk_{chunk_index:04d}" if total_chunks > 1 else ""
        
        # Calculate table range
        start_row = chunk_index * self.max_rows_per_chunk + 1
        end_row = start_row + len(df) - 1
        
        return {
            "table_id": table_id,
            "global_table_id": f"{os.path.basename(file_path)}_{sheet_name}_table_{table_id:04d}{chunk_suffix}",
            "content": table_content,
            "metadata": {
                "source_file": os.path.basename(file_path),
                "source_path": os.path.abspath(file_path),
                "source_sheet": sheet_name,
                "table_range": f"A{start_row}:{self._get_excel_column(len(df.columns))}{end_row}",
                "table_index": table_id,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "is_chunked": total_chunks > 1,
                "data_type": "table",
                "processing_timestamp": datetime.now().isoformat()
            },
            "statistics": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "non_null_cells": int(df.count().sum()),
                "null_cells": int(df.isnull().sum().sum()),
                "data_completeness": float(df.count().sum() / (len(df) * len(df.columns))) if not df.empty else 0.0,
                "word_count": self._count_words_in_dataframe(df)
            }
        }
    
    def _count_words_in_dataframe(self, df: pd.DataFrame) -> int:
        """Count total words in a DataFrame."""
        word_count = 0
        for column in df.columns:
            # Convert column to string and count words
            column_text = df[column].astype(str).str.cat(sep=' ')
            # Remove NaN strings and count words
            clean_text = column_text.replace('nan', '').replace('None', '').replace('NaN', '')
            words = clean_text.split()
            word_count += len([word for word in words if word.strip() and word not in ['nan', 'None', 'NaN']])
        return word_count
    
    def _chunk_large_table(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Chunk large tables while preserving data structure."""
        if len(df) <= self.max_rows_per_chunk:
            return [df]
        
        chunks = []
        for i in range(0, len(df), self.max_rows_per_chunk):
            chunk = df.iloc[i:i + self.max_rows_per_chunk].copy()
            chunks.append(chunk)
        
        return chunks
    
    def _should_chunk_table(self, df: pd.DataFrame) -> bool:
        """Determine if a table should be chunked based on size."""
        # Estimate memory usage
        memory_usage = df.memory_usage(deep=True).sum()
        size_mb = memory_usage / (1024 * 1024)
        
        return size_mb > self.max_size_mb or len(df) > self.max_rows_per_chunk
    
    def _get_excel_column(self, col_num: int) -> str:
        """Convert column number to Excel column letter."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result
    
    def _get_file_type(self, file_path: str) -> str:
        """Get file extension."""
        return Path(file_path).suffix.lower().lstrip('.')
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate MD5 hash for file integrity checking."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "unknown"
    
    def save_to_json(self, data: Dict[str, Any], output_file: str, 
                     pretty_print: bool = True, compress: bool = False) -> None:
        """Save processed data to JSON file."""
        print(f"💾 Saving to {output_file}...")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(output_file))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        indent = 2 if pretty_print else None
        separators = (',', ': ') if pretty_print else (',', ':')
        
        if compress:
            import gzip
            with gzip.open(f"{output_file}.gz", 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, separators=separators, ensure_ascii=False, default=str)
            print(f"✅ Compressed JSON saved to {output_file}.gz")
            file_size = os.path.getsize(f"{output_file}.gz")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, separators=separators, ensure_ascii=False, default=str)
            print(f"✅ JSON saved to {output_file}")
            file_size = os.path.getsize(output_file)
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

def find_excel_csv_files(input_path: str) -> List[str]:
    """Find all Excel and CSV files in the given path."""
    supported_extensions = ['.xlsx', '.xls', '.csv']
    
    if os.path.isfile(input_path):
        if any(input_path.lower().endswith(ext) for ext in supported_extensions):
            return [input_path]
        else:
            return []
    elif os.path.isdir(input_path):
        files = []
        for ext in supported_extensions:
            pattern = os.path.join(input_path, f"*{ext}")
            files.extend(glob.glob(pattern))
            # Also look in subdirectories
            pattern_recursive = os.path.join(input_path, f"**/*{ext}")
            files.extend(glob.glob(pattern_recursive, recursive=True))
        return list(set(files))  # Remove duplicates
    else:
        return []

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Enhanced Excel/CSV Parser - Convert Excel and CSV files to metadata-rich JSON with word counting and chunking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all Excel/CSV files in a folder
  python excel_parser_enhanced.py documents/ output.json
  
  # Process specific files with word counting
  python excel_parser_enhanced.py --files file1.xlsx file2.csv --output data.json
  
  # Custom chunking settings
  python excel_parser_enhanced.py documents/ --output data.json --max-rows 500 --max-size 5
        """
    )
    
    # Input arguments
    parser.add_argument('input', nargs='?', help='Input file or directory containing Excel/CSV files')
    parser.add_argument('output', nargs='?', help='Output JSON file path')
    parser.add_argument('--files', nargs='+', help='Specific files to process')
    parser.add_argument('-o', '--output', dest='output_file', help='Output JSON file path')
    
    # Processing options
    parser.add_argument('--no-preserve-dtypes', action='store_true',
                       help='Do not preserve original data types')
    parser.add_argument('--include-empty', action='store_true',
                       help='Include completely empty rows')
    parser.add_argument('--max-rows', type=int, default=1000,
                       help='Maximum rows per chunk (default: 1000)')
    parser.add_argument('--max-size', type=float, default=10.0,
                       help='Maximum size in MB before chunking (default: 10.0)')
    
    # Output options
    parser.add_argument('--compress', action='store_true',
                       help='Compress output as .gz file')
    parser.add_argument('--compact', action='store_true',
                       help='Compact JSON output (no pretty printing)')
    
    args = parser.parse_args()
    
    # Determine input files
    files = []
    if args.files:
        files = args.files
    elif args.input:
        files = find_excel_csv_files(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Determine output file
    output_file = args.output_file or args.output
    if not output_file:
        if args.input and os.path.isdir(args.input):
            output_file = f"{os.path.basename(args.input.rstrip('/'))}_enhanced_data.json"
        else:
            output_file = "excel_csv_enhanced_data.json"
    
    # Validate inputs
    if not files:
        print("❌ No Excel or CSV files found!")
        sys.exit(1)
    
    # Check if files exist
    valid_files = []
    for file_path in files:
        if os.path.exists(file_path) and any(file_path.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
            valid_files.append(file_path)
        else:
            print(f"⚠️  Warning: File not found or not supported: {file_path}")
    
    if not valid_files:
        print("❌ No valid Excel/CSV files to process!")
        sys.exit(1)
    
    # Initialize parser
    print("🚀 Initializing Enhanced Excel/CSV Parser...")
    print(f"📄 Files to process: {len(valid_files)}")
    print(f"🔧 Preserve data types: {'No' if args.no_preserve_dtypes else 'Yes'}")
    print(f"📝 Include empty rows: {'Yes' if args.include_empty else 'No'}")
    print(f"📦 Max rows per chunk: {args.max_rows}")
    print(f"💾 Max size before chunking: {args.max_size} MB")
    print(f"💾 Output: {output_file}")
    print()
    
    parser_instance = EnhancedExcelCSVParser(
        preserve_dtypes=not args.no_preserve_dtypes,
        include_empty_rows=args.include_empty,
        max_rows_per_chunk=args.max_rows,
        max_size_mb=args.max_size
    )
    
    # Process files
    try:
        result = parser_instance.process_files(valid_files)
        
        # Save to JSON
        parser_instance.save_to_json(
            result, 
            output_file,
            pretty_print=not args.compact,
            compress=args.compress
        )
        
        # Print summary
        print("\n📊 Processing Summary:")
        print(f"   📁 Files processed: {result['metadata']['total_files']}")
        print(f"   📄 Total sheets: {result['metadata']['total_sheets']}")
        print(f"   📋 Total tables: {result['metadata']['total_tables']}")
        print(f"   📊 Total rows: {result['metadata']['total_rows']}")
        print(f"   📝 Total words: {result['metadata']['total_words']}")
        print(f"   📈 Avg words per sheet: {result['metadata']['average_words_per_sheet']:.1f}")
        print(f"   💾 Output file: {output_file}")
        print("\n✅ Processing complete!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()