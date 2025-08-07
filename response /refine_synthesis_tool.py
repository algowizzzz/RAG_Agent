#!/usr/bin/env python3
"""
Refine Synthesis Tool
====================

A specialized tool for processing large retrieved content using the refine chain approach.
Handles token overflow by processing chunks in batches and iteratively refining responses.

Features:
- Gemini API integration for LLM calls
- Automatic batch size calculation based on token limits
- Smart chunk prioritization by relevance
- JSON input/output format
- Simple function interface for easy integration

Author: AI Development Team
Date: 2025-08-06
Version: 1.0
"""

import json
import os
import math
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import google.generativeai as genai
from pathlib import Path


@dataclass
class RefineConfig:
    """Configuration for refine synthesis process."""
    model_name: str = "gemini-1.5-pro"
    max_tokens_per_request: int = 1000000  # Gemini 1.5 Pro context limit
    response_reserve_tokens: int = 4000
    prompt_overhead_tokens: int = 1000
    average_chunk_tokens: int = 530  # Based on your data analysis
    temperature: float = 0.1
    
    @property
    def max_content_tokens(self) -> int:
        return self.max_tokens_per_request - self.response_reserve_tokens - self.prompt_overhead_tokens
    
    @property
    def chunks_per_batch(self) -> int:
        return self.max_content_tokens // self.average_chunk_tokens


class RefineSynthesisTool:
    """
    Main tool for refine-based synthesis of large content.
    
    Usage:
        tool = RefineSynthesisTool()
        result = tool.refine_synthesis(user_query, chunks)
    """
    
    def __init__(self, api_key: str = None, config: RefineConfig = None):
        """Initialize the refine synthesis tool."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(config.model_name if config else "gemini-1.5-pro")
        self.config = config or RefineConfig()
        
        print(f"✅ Refine Synthesis Tool initialized with {self.config.model_name}")
        print(f"   Max tokens per batch: {self.config.max_content_tokens:,}")
        print(f"   Chunks per batch: {self.config.chunks_per_batch}")

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text.split()) * 1.33  # Rough estimation

    def prioritize_chunks(self, chunks: List[str], user_query: str) -> List[str]:
        """Order chunks by relevance to user query for optimal refine processing."""
        query_keywords = set(user_query.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            relevance_score = len(query_keywords.intersection(chunk_words))
            scored_chunks.append((chunk, relevance_score))
        
        # Sort by relevance (highest first) for better initial foundation
        return [chunk for chunk, _ in sorted(scored_chunks, key=lambda x: x[1], reverse=True)]

    def create_batches(self, chunks: List[str]) -> List[List[str]]:
        """Create optimal batches from chunks based on token limits."""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for chunk in chunks:
            chunk_tokens = self.estimate_tokens(chunk)
            
            if current_tokens + chunk_tokens > self.config.max_content_tokens and current_batch:
                # Start new batch
                batches.append(current_batch)
                current_batch = [chunk]
                current_tokens = chunk_tokens
            else:
                current_batch.append(chunk)
                current_tokens += chunk_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches

    def create_initial_prompt(self, user_query: str, chunks: List[str], total_batches: int) -> str:
        """Create initial synthesis prompt for first batch."""
        chunks_text = "\n\n---CHUNK SEPARATOR---\n\n".join(chunks)
        
        return f"""You are a document analysis expert. Analyze the retrieved content and provide a comprehensive response to the user's query.

USER QUERY: {user_query}

RETRIEVED CONTENT (Batch 1 of {total_batches}):
{chunks_text}

INSTRUCTIONS:
1. Provide a thorough, well-structured response addressing the user's query
2. Use specific information from the retrieved content with citations where appropriate
3. Structure your response with clear headings and bullet points if helpful
4. Include relevant examples, definitions, or explanations
5. This is batch 1 of {total_batches} - additional content will follow to refine this response
6. Focus on accuracy and completeness based on the available content

Generate your comprehensive initial response:"""

    def create_refine_prompt(self, user_query: str, current_response: str, 
                           new_chunks: List[str], batch_num: int, total_batches: int) -> str:
        """Create refine prompt for subsequent batches."""
        new_content = "\n\n---CHUNK SEPARATOR---\n\n".join(new_chunks)
        
        return f"""You are refining a response with additional retrieved content. Improve and expand the current response using the new information.

USER QUERY: {user_query}

CURRENT RESPONSE:
{current_response}

NEW RETRIEVED CONTENT (Batch {batch_num} of {total_batches}):
{new_content}

INSTRUCTIONS:
1. Refine the current response by incorporating valuable new information
2. Correct any inconsistencies if new content contradicts previous information
3. Add important details, examples, or clarifications from the new content
4. Maintain the overall structure and coherent flow
5. Remove redundant information but ensure completeness
6. Integrate new citations or references appropriately
7. Keep the response focused on the user's query

Provide the refined and improved response:"""

    def gemini_generate(self, prompt: str) -> str:
        """Generate response using Gemini API with error handling."""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.response_reserve_tokens
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response.text:
                return response.text
            else:
                return "Error: No response generated from Gemini API"
                
        except Exception as e:
            return f"Error: Gemini API call failed - {str(e)}"

    def refine_synthesis(self, user_query: str, chunks: List[str], 
                        prioritize: bool = True) -> Dict[str, Any]:
        """
        Main refine synthesis function.
        
        Args:
            user_query: The user's question/request
            chunks: List of content chunks to process
            prioritize: Whether to reorder chunks by relevance
            
        Returns:
            Dict with response, metadata, and processing details
        """
        start_time = datetime.now()
        
        # Step 1: Prioritize chunks if requested
        if prioritize:
            chunks = self.prioritize_chunks(chunks, user_query)
            print(f"📊 Prioritized {len(chunks)} chunks by relevance")
        
        # Step 2: Determine processing strategy
        total_tokens = sum(self.estimate_tokens(chunk) for chunk in chunks)
        
        if total_tokens <= self.config.max_content_tokens:
            # Single batch processing
            print(f"✅ Single batch processing ({total_tokens:,} tokens)")
            batches = [chunks]
        else:
            # Multi-batch processing
            batches = self.create_batches(chunks)
            print(f"🔄 Multi-batch processing: {len(batches)} batches")
            print(f"   Total tokens: {total_tokens:,}")
        
        # Step 3: Initial synthesis with first batch
        print(f"🚀 Starting synthesis with batch 1/{len(batches)} ({len(batches[0])} chunks)")
        
        initial_prompt = self.create_initial_prompt(user_query, batches[0], len(batches))
        current_response = self.gemini_generate(initial_prompt)
        
        processing_log = [{
            'batch_number': 1,
            'chunk_count': len(batches[0]),
            'processing_time': (datetime.now() - start_time).total_seconds(),
            'action': 'initial_synthesis'
        }]
        
        # Step 4: Refine with subsequent batches
        for i, batch in enumerate(batches[1:], 2):
            batch_start = datetime.now()
            print(f"🔄 Refining with batch {i}/{len(batches)} ({len(batch)} chunks)")
            
            refine_prompt = self.create_refine_prompt(
                user_query, current_response, batch, i, len(batches)
            )
            
            refined_response = self.gemini_generate(refine_prompt)
            current_response = refined_response
            
            processing_log.append({
                'batch_number': i,
                'chunk_count': len(batch),
                'processing_time': (datetime.now() - batch_start).total_seconds(),
                'action': 'refine_synthesis'
            })
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Return comprehensive result
        return {
            'response': current_response,
            'metadata': {
                'user_query': user_query,
                'total_chunks': len(chunks),
                'total_batches': len(batches),
                'total_tokens_estimated': total_tokens,
                'processing_strategy': 'single_batch' if len(batches) == 1 else 'multi_batch',
                'prioritized': prioritize,
                'total_processing_time': total_time
            },
            'processing_log': processing_log,
            'config': {
                'model_name': self.config.model_name,
                'chunks_per_batch_limit': self.config.chunks_per_batch,
                'max_content_tokens': self.config.max_content_tokens
            }
        }

    def process_json_file(self, json_file_path: str, user_query: str = None) -> Dict[str, Any]:
        """
        Process a JSON file from your retrieval system.
        
        Expected JSON format from your langchain_json_tool outputs.
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract chunks from your JSON format
        chunks = self.extract_chunks_from_json(data)
        
        # Use provided query or infer from test data
        if not user_query:
            user_query = self.infer_query_from_json(data)
        
        print(f"📄 Processing: {Path(json_file_path).name}")
        print(f"❓ Query: {user_query}")
        print(f"📦 Extracted {len(chunks)} chunks")
        
        return self.refine_synthesis(user_query, chunks)

    def extract_chunks_from_json(self, data: Dict[str, Any]) -> List[str]:
        """Extract content chunks from your JSON retrieval format."""
        chunks = []
        
        response_data = data.get('response', {})
        detailed_results = response_data.get('detailed_results', {})
        
        # Handle different content types from your system
        if detailed_results.get('type') == 'pdf_chunk':
            # Single PDF chunk
            content = detailed_results.get('content', '')
            if content:
                chunks.append(content)
                
        elif detailed_results.get('type') == 'excel_table':
            # Excel data - format as readable text
            excel_content = detailed_results.get('content', {})
            if 'data' in excel_content:
                formatted_content = self.format_excel_data(excel_content)
                chunks.append(formatted_content)
                
        elif 'results' in detailed_results:
            # Search results with multiple chunks
            results = detailed_results.get('results', [])
            for result in results:
                if 'match_preview' in result:
                    chunks.append(result['match_preview'])
                elif 'content' in result:
                    chunks.append(result['content'])
                    
        elif 'items' in detailed_results:
            # Full file results with items array
            items = detailed_results.get('items', [])
            for item in items:
                if 'content' in item:
                    chunks.append(item['content'])
                    
        elif 'files' in detailed_results:
            # File discovery results
            files = detailed_results.get('files', [])
            content = f"Available files: {', '.join(files)}"
            chunks.append(content)
        
        return chunks

    def format_excel_data(self, excel_content: Dict[str, Any]) -> str:
        """Format Excel data into readable text chunk."""
        if 'data' not in excel_content:
            return "No Excel data available"
        
        data = excel_content['data']
        columns = excel_content.get('columns', [])
        
        formatted = f"Excel Data - Columns: {', '.join(columns)}\n\n"
        
        for i, row in enumerate(data):
            formatted += f"Row {i+1}:\n"
            for col in columns:
                value = row.get(col, 'N/A')
                formatted += f"  {col}: {value}\n"
            formatted += "\n"
        
        return formatted

    def infer_query_from_json(self, data: Dict[str, Any]) -> str:
        """Infer user query from test data."""
        test_name = data.get('test_name', '')
        expected = data.get('expected', '')
        operation = data.get('test_params', {}).get('operation', '')
        
        if expected and 'Natural language:' in expected:
            return expected.replace('Natural language:', '').strip()
        elif 'file discovery' in test_name.lower():
            return "What files are available in the system?"
        elif 'excel data' in test_name.lower():
            return "Show me the Excel data and provide analysis"
        elif 'search content' in test_name.lower():
            return "Search for relevant content and provide summary"
        else:
            return f"Process and analyze the content from {test_name}"


# Simple function interface for easy integration
def simple_refine_synthesis(user_query: str, chunks: List[str], 
                          api_key: str = None) -> str:
    """
    Simple function interface for refine synthesis.
    
    Args:
        user_query: User's question
        chunks: List of content chunks
        api_key: Gemini API key (optional if set in env)
    
    Returns:
        Generated response string
    """
    tool = RefineSynthesisTool(api_key=api_key)
    result = tool.refine_synthesis(user_query, chunks)
    return result['response']


def process_json_file_simple(json_file_path: str, user_query: str = None, 
                           api_key: str = None) -> str:
    """
    Simple function to process a JSON file from your retrieval system.
    
    Args:
        json_file_path: Path to JSON file
        user_query: Optional user query
        api_key: Gemini API key (optional if set in env)
    
    Returns:
        Generated response string
    """
    tool = RefineSynthesisTool(api_key=api_key)
    result = tool.process_json_file(json_file_path, user_query)
    return result['response']


def main():
    """Main function for testing and CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refine Synthesis Tool')
    parser.add_argument('--json-file', help='JSON file to process')
    parser.add_argument('--query', help='User query')
    parser.add_argument('--api-key', help='Gemini API key')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--test', action='store_true', help='Run test with sample data')
    
    args = parser.parse_args()
    
    try:
        tool = RefineSynthesisTool(api_key=args.api_key)
        
        if args.test:
            # Run test with sample chunks
            test_chunks = [
                "OSFI Capital Adequacy Requirements specify minimum capital ratios for banks.",
                "Risk-weighted assets must be calculated using standardized or IRB approaches.",
                "The capital conservation buffer is set at 2.5% of risk-weighted assets."
            ]
            result = tool.refine_synthesis("What are OSFI capital requirements?", test_chunks)
            
        elif args.json_file:
            result = tool.process_json_file(args.json_file, args.query)
            
        else:
            print("❌ Please provide --json-file or use --test")
            return 1
        
        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"📄 Results saved to: {args.output}")
        else:
            print(f"\n📝 Response:")
            print("="*80)
            print(result['response'])
            print("="*80)
            print(f"\n📊 Metadata:")
            print(f"   Chunks: {result['metadata']['total_chunks']}")
            print(f"   Batches: {result['metadata']['total_batches']}")
            print(f"   Strategy: {result['metadata']['processing_strategy']}")
            print(f"   Time: {result['metadata']['total_processing_time']:.2f}s")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())