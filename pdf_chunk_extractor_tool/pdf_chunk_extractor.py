#!/usr/bin/env python3
"""
PDF Chunk Extractor Tool
A standalone tool that processes PDF files into metadata-rich JSON chunks
similar to the OSFI CAR project implementation.

Usage:
    python pdf_chunk_extractor.py input_folder/ output_file.json
    python pdf_chunk_extractor.py --files file1.pdf file2.pdf --output chunks.json
    python pdf_chunk_extractor.py --help
"""

import os
import sys
import glob
import json
import argparse
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import required libraries
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
    sys.exit(1)

class PDFChunkExtractor:
    """Standalone PDF processor that chunks documents into metadata-rich JSON format."""
    
    def __init__(self, 
                 chunk_size: int = 5000, 
                 chunk_overlap: int = 100,
                 add_embeddings: bool = False,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the PDF chunk extractor.
        
        Args:
            chunk_size: Size of text chunks in tokens (default: 5000)
            chunk_overlap: Overlap between chunks in tokens (default: 100)
            add_embeddings: Whether to generate embeddings for chunks (default: False)
            embedding_model: Embedding model to use if add_embeddings is True
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.add_embeddings = add_embeddings
        self.embedding_model = embedding_model
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize embeddings if requested
        self.embeddings = None
        if add_embeddings:
            self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embedding model."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
            print(f"✅ Embeddings initialized: {self.embedding_model}")
        except ImportError:
            print("⚠️  Warning: HuggingFace embeddings not available. Install with:")
            print("pip install langchain-huggingface")
            self.add_embeddings = False
    
    def process_pdf_files(self, pdf_files: List[str]) -> Dict[str, Any]:
        """
        Process multiple PDF files into chunked JSON format.
        
        Args:
            pdf_files: List of PDF file paths to process
            
        Returns:
            Dictionary with document metadata and chunks
        """
        print(f"🔄 Processing {len(pdf_files)} PDF files...")
        
        # Initialize result structure
        result = {
            "metadata": {
                "processing_timestamp": datetime.now().isoformat(),
                "source_type": "pdf_chunk_extractor",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "embedding_model": self.embedding_model if self.add_embeddings else None,
                "total_files": len(pdf_files),
                "files_processed": [],
                "total_chunks": 0,
                "total_pages": 0,
                "total_words": 0,
                "total_sheets": "N/A",  # Not applicable for PDFs
                "total_tables": "N/A",  # Not applicable for PDFs
                "total_rows": "N/A",   # Not applicable for PDFs
                "word_count_by_sheet": "N/A",  # Not applicable for PDFs
                "average_chunks_per_file": 0
            },
            "documents": [],
            "chunks": []
        }
        
        chunk_id = 0
        
        for pdf_file in pdf_files:
            try:
                file_result = self._process_single_pdf(pdf_file, chunk_id)
                
                # Update metadata
                result["metadata"]["files_processed"].append({
                    "filename": os.path.basename(pdf_file),
                    "file_type": "pdf",
                    "full_path": os.path.abspath(pdf_file),
                    "pages": file_result["pages"],
                    "chunks": file_result["chunks_count"],
                    "file_size_bytes": os.path.getsize(pdf_file),
                    "file_hash": self._get_file_hash(pdf_file),
                    "total_words": file_result["total_words"],
                    "word_count_by_sheet": "N/A",  # Not applicable for PDFs
                    "is_chunked": "N/A",  # Always chunked for PDFs
                    "chunk_count": file_result["chunks_count"]
                })
                
                result["metadata"]["total_pages"] += file_result["pages"]
                result["metadata"]["total_chunks"] += file_result["chunks_count"]
                result["metadata"]["total_words"] += file_result["total_words"]
                
                # Add document info
                result["documents"].append(file_result["document_info"])
                
                # Add chunks
                result["chunks"].extend(file_result["chunks"])
                
                # Update chunk counter
                chunk_id += file_result["chunks_count"]
                
                print(f"✅ Processed {os.path.basename(pdf_file)}: {file_result['pages']} pages, {file_result['chunks_count']} chunks, {file_result['total_words']} words")
                
            except Exception as e:
                print(f"❌ Error processing {pdf_file}: {e}")
                result["metadata"]["files_processed"].append({
                    "filename": os.path.basename(pdf_file),
                    "full_path": os.path.abspath(pdf_file),
                    "error": str(e),
                    "status": "failed"
                })
        
        # Calculate summary statistics
        result["metadata"]["average_chunks_per_file"] = (
            result["metadata"]["total_chunks"] / len([f for f in result["metadata"]["files_processed"] if "error" not in f])
            if result["metadata"]["files_processed"] else 0
        )
        
        print(f"🎯 Processing complete: {result['metadata']['total_chunks']} total chunks from {result['metadata']['total_pages']} pages ({result['metadata']['total_words']} total words)")
        
        return result
    
    def _process_single_pdf(self, pdf_file: str, start_chunk_id: int) -> Dict[str, Any]:
        """Process a single PDF file into chunks."""
        
        # Load PDF
        loader = PyPDFLoader(pdf_file)
        documents = loader.load()
        
        # Add enhanced metadata to each document
        for i, doc in enumerate(documents):
            doc.metadata.update({
                'source_file': os.path.basename(pdf_file),
                'source_path': os.path.abspath(pdf_file),
                'page_number': i + 1,
                'total_pages': len(documents),
                'processing_timestamp': datetime.now().isoformat()
            })
        
        # Split documents into chunks
        doc_splits = self.text_splitter.split_documents(documents)
        
        # Create chunk data
        chunks = []
        for i, chunk in enumerate(doc_splits):
            chunk_data = {
                "chunk_id": start_chunk_id + i,
                "global_chunk_id": f"{os.path.basename(pdf_file)}_chunk_{i:04d}",
                "content": chunk.page_content,
                "metadata": {
                    "source_file": chunk.metadata.get('source_file'),
                    "source_path": chunk.metadata.get('source_path'),
                    "page_number": chunk.metadata.get('page', 'unknown'),
                    "chunk_index": i,
                    "chunk_size_chars": len(chunk.page_content),
                    "chunk_size_words": len(chunk.page_content.split()),
                    "chunk_hash": hashlib.md5(chunk.page_content.encode()).hexdigest(),
                    "processing_timestamp": chunk.metadata.get('processing_timestamp')
                },
                "statistics": {
                    "character_count": len(chunk.page_content),
                    "word_count": len(chunk.page_content.split()),
                    "sentence_count": len([s for s in chunk.page_content.split('.') if s.strip()]),
                    "paragraph_count": len([p for p in chunk.page_content.split('\n\n') if p.strip()])
                }
            }
            
            # Add embeddings if requested
            if self.add_embeddings and self.embeddings:
                try:
                    embedding = self.embeddings.embed_query(chunk.page_content)
                    chunk_data["embedding"] = {
                        "model": self.embedding_model,
                        "vector": embedding,
                        "dimension": len(embedding)
                    }
                except Exception as e:
                    print(f"⚠️  Warning: Could not generate embedding for chunk {i}: {e}")
            
            chunks.append(chunk_data)
        
        # Calculate total words
        total_words = sum(chunk["statistics"]["word_count"] for chunk in chunks)
        
        return {
            "document_info": {
                "filename": os.path.basename(pdf_file),
                "file_type": "pdf",
                "full_path": os.path.abspath(pdf_file),
                "pages": len(documents),
                "chunks_count": len(chunks),
                "file_size_bytes": os.path.getsize(pdf_file),
                "file_hash": self._get_file_hash(pdf_file),
                "processing_timestamp": datetime.now().isoformat(),
                "total_words": total_words,
                "word_count_by_sheet": "N/A",  # Not applicable for PDFs
                "is_chunked": True,  # PDFs are always chunked
                "chunk_count": len(chunks)
            },
            "chunks": chunks,
            "pages": len(documents),
            "chunks_count": len(chunks),
            "total_words": total_words
        }
    
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
        """
        Save processed data to JSON file.
        
        Args:
            data: Processed document data
            output_file: Output JSON file path
            pretty_print: Whether to format JSON with indentation
            compress: Whether to compress the output (for large files)
        """
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
                json.dump(data, f, indent=indent, separators=separators, ensure_ascii=False)
            print(f"✅ Compressed JSON saved to {output_file}.gz")
            file_size = os.path.getsize(f"{output_file}.gz")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, separators=separators, ensure_ascii=False)
            print(f"✅ JSON saved to {output_file}")
            file_size = os.path.getsize(output_file)
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

def find_pdf_files(input_path: str) -> List[str]:
    """Find all PDF files in the given path."""
    if os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
        return [input_path]
    elif os.path.isdir(input_path):
        pdf_pattern = os.path.join(input_path, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        # Also look in subdirectories
        pdf_pattern_recursive = os.path.join(input_path, "**/*.pdf")
        pdf_files.extend(glob.glob(pdf_pattern_recursive, recursive=True))
        return list(set(pdf_files))  # Remove duplicates
    else:
        return []

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="PDF Chunk Extractor - Convert PDF files to metadata-rich JSON chunks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in a folder
  python pdf_chunk_extractor.py documents/ output.json
  
  # Process specific files
  python pdf_chunk_extractor.py --files file1.pdf file2.pdf --output chunks.json
  
  # Include embeddings and compress output
  python pdf_chunk_extractor.py documents/ --output chunks.json --embeddings --compress
  
  # Custom chunk size
  python pdf_chunk_extractor.py documents/ --output chunks.json --chunk-size 1500 --overlap 150
        """
    )
    
    # Input arguments
    parser.add_argument('input', nargs='?', help='Input PDF file or directory containing PDFs')
    parser.add_argument('output', nargs='?', help='Output JSON file path')
    parser.add_argument('--files', nargs='+', help='Specific PDF files to process')
    parser.add_argument('-o', '--output', dest='output_file', help='Output JSON file path')
    
    # Processing options
    parser.add_argument('--chunk-size', type=int, default=5000, 
                       help='Chunk size in tokens (default: 5000)')
    parser.add_argument('--overlap', type=int, default=100,
                       help='Overlap between chunks in tokens (default: 100)')
    parser.add_argument('--embeddings', action='store_true',
                       help='Generate embeddings for chunks (requires langchain-huggingface)')
    parser.add_argument('--embedding-model', default='all-MiniLM-L6-v2',
                       help='Embedding model to use (default: all-MiniLM-L6-v2)')
    
    # Output options
    parser.add_argument('--compress', action='store_true',
                       help='Compress output as .gz file')
    parser.add_argument('--compact', action='store_true',
                       help='Compact JSON output (no pretty printing)')
    
    args = parser.parse_args()
    
    # Determine input files
    pdf_files = []
    if args.files:
        pdf_files = args.files
    elif args.input:
        pdf_files = find_pdf_files(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Determine output file
    output_file = args.output_file or args.output
    if not output_file:
        if args.input and os.path.isdir(args.input):
            output_file = f"{os.path.basename(args.input.rstrip('/'))}_chunks.json"
        else:
            output_file = "pdf_chunks.json"
    
    # Validate inputs
    if not pdf_files:
        print("❌ No PDF files found!")
        sys.exit(1)
    
    # Check if PDF files exist
    valid_files = []
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file) and pdf_file.lower().endswith('.pdf'):
            valid_files.append(pdf_file)
        else:
            print(f"⚠️  Warning: File not found or not a PDF: {pdf_file}")
    
    if not valid_files:
        print("❌ No valid PDF files to process!")
        sys.exit(1)
    
    # Initialize extractor
    print("🚀 Initializing PDF Chunk Extractor...")
    print(f"📄 Files to process: {len(valid_files)}")
    print(f"⚙️  Chunk size: {args.chunk_size} tokens")
    print(f"🔄 Overlap: {args.overlap} tokens")
    print(f"🧠 Embeddings: {'Yes' if args.embeddings else 'No'}")
    if args.embeddings:
        print(f"🤖 Embedding model: {args.embedding_model}")
    print(f"💾 Output: {output_file}")
    print()
    
    extractor = PDFChunkExtractor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        add_embeddings=args.embeddings,
        embedding_model=args.embedding_model
    )
    
    # Process files
    try:
        result = extractor.process_pdf_files(valid_files)
        
        # Save to JSON
        extractor.save_to_json(
            result, 
            output_file,
            pretty_print=not args.compact,
            compress=args.compress
        )
        
        # Print summary
        print("\n📊 Processing Summary:")
        print(f"   📁 Files processed: {result['metadata']['total_files']}")
        print(f"   📄 Total pages: {result['metadata']['total_pages']}")
        print(f"   🔤 Total chunks: {result['metadata']['total_chunks']}")
        print(f"   📊 Avg chunks per file: {result['metadata']['average_chunks_per_file']:.1f}")
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