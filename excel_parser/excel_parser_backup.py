#!/usr/bin/env python3
"""
Enhanced Excel/CSV Parser Tool with Word Counting and Chunking
"""

import os
import sys
import glob
import json
import argparse
import hashlib
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class EnhancedExcelCSVParser:
    """Enhanced Excel/CSV processor with word counting and chunking."""
    
    def __init__(self, preserve_dtypes: bool = True, max_rows_per_chunk: int = 100):
        self.preserve_dtypes = preserve_dtypes
        self.max_rows_per_chunk = max_rows_per_chunk
    
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple Excel/CSV files into JSON format."""
        print(f"🔄 Processing {len(file_paths)} files...")
        
        result = {
            "metadata": {
                "processing_timestamp": datetime.now().isoformat(),
                "source_type": "excel_csv_enhanced",
                "total_files": len(file_paths),
                "files_processed": [],
                "total_sheets": 0,
                "total_tables": 0,
                "total_rows": 0,
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
                
                result["metadata"]["files_processed"].append({
                    "filename": os.path.basename(file_path),
                    "file_type": self._get_file_type(file_path),
                    "total_words": file_result["total_words"],
                    "word_count_by_sheet": file_result["word_count_by_sheet"]
                })
                
                result["metadata"]["total_words"] += file_result["total_words"]
                result["metadata"]["word_count_by_sheet"].extend(file_result["word_count_by_sheet"])
                result["metadata"]["total_tables"] += file_result["tables_count"]
                result["metadata"]["total_sheets"] += file_result["sheets_count"]
                
                result["documents"].append(file_result["document_info"])
                result["data"].extend(file_result["tables"])
                
                table_id += file_result["tables_count"]
                
                print(f"✅ Processed {os.path.basename(file_path)}: {file_result['total_words']} words")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
        
        return result
    
    def _process_single_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process a single file."""
        file_type = self._get_file_type(file_path)
        
        if file_type == "csv":
            return self._process_csv_file(file_path, start_table_id)
        elif file_type in ["xlsx", "xls"]:
            return self._process_excel_file(file_path, start_table_id)
    
    def _process_csv_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process a CSV file."""
        df = pd.read_csv(file_path)
        word_count = self._count_words_in_dataframe(df)
        
        # Check if chunking is needed
        tables = []
        if len(df) > self.max_rows_per_chunk:
            print(f"   📦 Chunking large CSV ({len(df)} rows into chunks of {self.max_rows_per_chunk})")
            chunks = self._chunk_dataframe(df)
            
            for i, chunk_df in enumerate(chunks):
                table_data = self._dataframe_to_nested_json(chunk_df, file_path, "CSV_Data", start_table_id + i, i, len(chunks))
                tables.append(table_data)
        else:
            table_data = self._dataframe_to_nested_json(df, file_path, "CSV_Data", start_table_id)
            tables.append(table_data)
        
        return {
            "document_info": {
                "filename": os.path.basename(file_path),
                "file_type": "csv",
                "total_words": word_count,
                "word_count_by_sheet": [{"sheet_name": "CSV_Data", "word_count": word_count}],
                "is_chunked": len(tables) > 1,
                "chunk_count": len(tables)
            },
            "tables": tables,
            "sheets_count": 1,
            "tables_count": len(tables),
            "total_words": word_count,
            "word_count_by_sheet": [{"sheet_name": "CSV_Data", "word_count": word_count}]
        }
    
    def _process_excel_file(self, file_path: str, start_table_id: int) -> Dict[str, Any]:
        """Process an Excel file."""
        sheet_dict = pd.read_excel(file_path, sheet_name=None)
        
        tables = []
        total_words = 0
        word_count_by_sheet = []
        table_id = start_table_id
        
        for sheet_name, df in sheet_dict.items():
            if not df.empty:
                sheet_word_count = self._count_words_in_dataframe(df)
                word_count_by_sheet.append({"sheet_name": sheet_name, "word_count": sheet_word_count})
                total_words += sheet_word_count
                
                table_data = self._dataframe_to_nested_json(df, file_path, sheet_name, table_id)
                tables.append(table_data)
                table_id += 1
        
        return {
            "document_info": {
                "filename": os.path.basename(file_path),
                "file_type": self._get_file_type(file_path),
                "total_words": total_words,
                "word_count_by_sheet": word_count_by_sheet,
                "sheet_names": list(sheet_dict.keys())
            },
            "tables": tables,
            "sheets_count": len(sheet_dict),
            "tables_count": len(tables),
            "total_words": total_words,
            "word_count_by_sheet": word_count_by_sheet
        }
    
    def _dataframe_to_nested_json(self, df: pd.DataFrame, file_path: str, sheet_name: str, table_id: int, chunk_index: int = 0, total_chunks: int = 1) -> Dict[str, Any]:
        """Convert DataFrame to nested JSON."""
        table_content = {
            "columns": df.columns.tolist(),
            "data": df.to_dict('records'),
            "shape": list(df.shape)
        }
        
        # Create chunk identifier
        chunk_suffix = f"_chunk_{chunk_index:04d}" if total_chunks > 1 else ""
        
        return {
            "table_id": table_id,
            "global_table_id": f"{os.path.basename(file_path)}_{sheet_name}_table_{table_id:04d}{chunk_suffix}",
            "content": table_content,
            "metadata": {
                "source_file": os.path.basename(file_path),
                "source_sheet": sheet_name,
                "data_type": "table",
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "is_chunked": total_chunks > 1
            },
            "statistics": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "word_count": self._count_words_in_dataframe(df)
            }
        }
    
    def _count_words_in_dataframe(self, df: pd.DataFrame) -> int:
        """Count total words in a DataFrame."""
        word_count = 0
        for column in df.columns:
            column_text = df[column].astype(str).str.cat(sep=' ')
            clean_text = column_text.replace('nan', '').replace('None', '').replace('NaN', '')
            words = clean_text.split()
            word_count += len([word for word in words if word.strip() and word not in ['nan', 'None', 'NaN']])
        return word_count
    
    def _chunk_dataframe(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Chunk a large DataFrame into smaller pieces."""
        chunks = []
        for i in range(0, len(df), self.max_rows_per_chunk):
            chunk = df.iloc[i:i + self.max_rows_per_chunk].copy()
            chunks.append(chunk)
        return chunks
    
    def _get_file_type(self, file_path: str) -> str:
        """Get file extension."""
        return Path(file_path).suffix.lower().lstrip('.')
    
    def save_to_json(self, data: Dict[str, Any], output_file: str) -> None:
        """Save to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ JSON saved to {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced Excel/CSV Parser with Word Counting")
    parser.add_argument('--files', nargs='+', help='Files to process')
    parser.add_argument('--output', help='Output file')
    
    args = parser.parse_args()
    
    if not args.files or not args.output:
        print("Usage: python excel_parser_enhanced.py --files file1.csv file2.xlsx --output output.json")
        sys.exit(1)
    
    parser_instance = EnhancedExcelCSVParser()
    result = parser_instance.process_files(args.files)
    parser_instance.save_to_json(result, args.output)
    
    print(f"\n📊 Summary: {result['metadata']['total_words']} total words")
    for sheet_info in result['metadata']['word_count_by_sheet']:
        print(f"   📄 {sheet_info['sheet_name']}: {sheet_info['word_count']} words")

if __name__ == "__main__":
    main()