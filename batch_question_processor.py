#!/usr/bin/env python3
"""
Batch Question Processor for Agent Content Package
=================================================

This script processes a batch of questions from a file using the intelligent
discovery and synthesis tool, and generates a comprehensive markdown report
with all answers.

Features:
- Reads questions from test_questions.txt
- Processes each question with intelligent size-based processing
- Generates detailed markdown report with timing and metadata
- Saves results to output_reports/ directory
- Provides progress tracking and error handling

Usage:
    python batch_question_processor.py [questions_file] [output_file]
    
Arguments:
    questions_file: Path to questions file (default: ../test_questions.txt)
    output_file: Output filename prefix (default: Batch_Questions_Report)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool


def load_questions(questions_file: str) -> List[str]:
    """Load questions from a text file, filtering out empty lines."""
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f.readlines()]
        
        # Filter out empty lines and questions that are too short
        valid_questions = [q for q in questions if q and len(q.strip()) > 5]
        
        print(f"📄 Loaded {len(valid_questions)} valid questions from {questions_file}")
        return valid_questions
        
    except FileNotFoundError:
        print(f"❌ Questions file not found: {questions_file}")
        return []
    except Exception as e:
        print(f"❌ Error reading questions file: {str(e)}")
        return []


def extract_document_sources(result_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract document sources and metadata from processing results."""
    sources = []
    
    try:
        # Extract from detailed reasoning if available
        if 'detailed_reasoning' in result_data:
            reasoning = result_data['detailed_reasoning']
            
            # Look for discovery results
            if 'discovery_results' in reasoning:
                discovery = reasoning['discovery_results']
                if 'available_documents' in discovery:
                    for doc in discovery['available_documents']:
                        sources.append({
                            'type': 'discovery',
                            'filename': doc.get('filename', 'Unknown'),
                            'content_type': doc.get('content_type', 'Unknown'),
                            'page_count': str(doc.get('page_count', 'N/A'))
                        })
            
            # Look for retrieved content chunks
            if 'llm_decision_making_process' in reasoning:
                for step in reasoning['llm_decision_making_process']:
                    if step.get('phase') == 'content_retrieval' and 'retrieved_content' in step:
                        for chunk in step['retrieved_content'][:5]:  # Limit to first 5 for brevity
                            if 'source_file' in chunk:
                                sources.append({
                                    'type': 'retrieved_chunk',
                                    'filename': chunk.get('source_file', 'Unknown'),
                                    'page': str(chunk.get('page', 'N/A')),
                                    'relevance_score': f"{chunk.get('relevance_score', 0):.3f}" if 'relevance_score' in chunk else 'N/A'
                                })
        
        # Remove duplicates based on filename
        seen_files = set()
        unique_sources = []
        for source in sources:
            file_key = f"{source['filename']}_{source.get('page', '')}"
            if file_key not in seen_files:
                seen_files.add(file_key)
                unique_sources.append(source)
                
        return unique_sources[:10]  # Limit to top 10 sources
        
    except Exception as e:
        print(f"⚠️  Warning: Could not extract document sources: {str(e)}")
        return []


def process_single_question(tool, question: str, question_num: int, total_questions: int) -> Dict[str, Any]:
    """Process a single question and return structured results."""
    
    print(f"\n{'='*60}")
    print(f"🔍 Question {question_num}/{total_questions}")
    print(f"{'='*60}")
    print(f"❓ {question}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        # Process the question with intelligent processing
        result = tool._run(
            user_query=question,
            include_reasoning=True,
            max_results=40  # Increased for comprehensive answers
        )
        
        result_data = json.loads(result)
        end_time = datetime.now()
        
        if result_data['status'] == 'SUCCESS':
            processing_time = result_data['processing_summary']['total_processing_time_seconds']
            chunks_processed = result_data['processing_summary']['total_chunks_processed']
            strategy = result_data['processing_summary']['processing_strategy']
            
            # Extract document sources
            document_sources = extract_document_sources(result_data)
            
            print(f"✅ Success!")
            print(f"📊 Strategy: {strategy}")
            print(f"⏱️  Time: {processing_time:.2f}s")
            print(f"📦 Chunks: {chunks_processed}")
            print(f"📝 Response: {len(result_data['ai_response'])} characters")
            print(f"📚 Sources: {len(document_sources)} documents")
            
            return {
                "question_number": question_num,
                "question": question,
                "status": "SUCCESS",
                "answer": result_data['ai_response'],
                "processing_time": processing_time,
                "chunks_processed": chunks_processed,
                "processing_strategy": strategy,
                "total_time": (end_time - start_time).total_seconds(),
                "document_sources": document_sources,
                "metadata": result_data.get('processing_summary', {}),
                "reasoning": result_data.get('detailed_reasoning', {}) if result_data.get('detailed_reasoning') else None
            }
        else:
            print(f"❌ Failed: {result_data.get('error_message', 'Unknown error')}")
            return {
                "question_number": question_num,
                "question": question,
                "status": "ERROR",
                "error": result_data.get('error_message', 'Unknown error'),
                "total_time": (end_time - start_time).total_seconds(),
                "document_sources": []
            }
            
    except Exception as e:
        end_time = datetime.now()
        print(f"❌ Exception: {str(e)}")
        return {
            "question_number": question_num,
            "question": question,
            "status": "EXCEPTION",
            "error": str(e),
            "total_time": (end_time - start_time).total_seconds(),
            "document_sources": []
        }


def generate_markdown_report(results: List[Dict[str, Any]], 
                           questions_file: str, 
                           output_file: str) -> str:
    """Generate a comprehensive markdown report from batch processing results."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate summary statistics
    total_questions = len(results)
    successful = len([r for r in results if r['status'] == 'SUCCESS'])
    failed = total_questions - successful
    total_time = sum(r.get('total_time', 0) for r in results)
    avg_time = total_time / total_questions if total_questions > 0 else 0
    
    # Processing strategy breakdown
    strategies = {}
    for r in results:
        if r['status'] == 'SUCCESS':
            strategy = r.get('processing_strategy', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
    
    # Generate markdown content
    markdown_content = f"""# Batch Question Processing Report

**Generated:** {timestamp}  
**Source:** {questions_file}  
**Tool:** Agent Content Package - Intelligent Discovery and Synthesis  
**Processing Mode:** Intelligent Size-Based Processing (Direct Synthesis <100k words, Targeted Retrieval ≥100k words)

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Questions** | {total_questions} |
| **Successful Answers** | {successful} |
| **Failed/Errors** | {failed} |
| **Success Rate** | {(successful/total_questions*100):.1f}% |
| **Total Processing Time** | {total_time:.2f} seconds |
| **Average Time per Question** | {avg_time:.2f} seconds |

### Processing Strategy Breakdown

"""
    
    for strategy, count in strategies.items():
        percentage = (count / successful * 100) if successful > 0 else 0
        markdown_content += f"- **{strategy}**: {count} questions ({percentage:.1f}%)\n"
    
    markdown_content += f"""

---

## Detailed Question and Answer Analysis

"""
    
    # Add each question and answer
    for result in results:
        q_num = result['question_number']
        question = result['question']
        status = result['status']
        
        markdown_content += f"""### Question {q_num}

**Query:** {question}

**Status:** {'✅ SUCCESS' if status == 'SUCCESS' else '❌ ' + status}

"""
        
        if status == 'SUCCESS':
            processing_time = result.get('processing_time', 0)
            chunks = result.get('chunks_processed', 0)
            strategy = result.get('processing_strategy', 'unknown')
            document_sources = result.get('document_sources', [])
            
            markdown_content += f"""**Processing Details:**
- Strategy: {strategy}
- Processing Time: {processing_time:.2f}s
- Chunks Processed: {chunks}
- Document Sources: {len(document_sources)} files

**Document Sources:**

"""
            
            if document_sources:
                markdown_content += "| Document | Type | Page/Info | Relevance |\n"
                markdown_content += "|----------|------|-----------|----------|\n"
                for source in document_sources:
                    doc_name = source.get('filename', 'Unknown')
                    doc_type = source.get('type', 'Unknown')
                    page_info = source.get('page', source.get('page_count', 'N/A'))
                    relevance = source.get('relevance_score', 'N/A')
                    markdown_content += f"| {doc_name} | {doc_type} | {page_info} | {relevance} |\n"
                markdown_content += "\n"
            else:
                markdown_content += "*No specific document sources captured*\n\n"
            
            markdown_content += f"""**Answer:**

{result['answer']}

"""
        else:
            error = result.get('error', 'Unknown error')
            markdown_content += f"""**Error:** {error}

"""
        
        markdown_content += "---\n\n"
    
    # Add technical appendix
    markdown_content += f"""## Technical Appendix

### Processing Configuration
- **Tool Version:** Agent Content Package v1.0.0
- **LLM:** Gemini 1.5 Pro
- **Processing Method:** Intelligent Size-Based Processing
- **Word Threshold:** 100,000 words
- **Max Results per Query:** 40 chunks

### Performance Metrics
- **Fastest Query:** {min([r.get('processing_time', 0) for r in results if r['status'] == 'SUCCESS'], default=0):.2f}s
- **Slowest Query:** {max([r.get('processing_time', 0) for r in results if r['status'] == 'SUCCESS'], default=0):.2f}s
- **Total Chunks Processed:** {sum([r.get('chunks_processed', 0) for r in results if r['status'] == 'SUCCESS'])}

### Data Source
- **Input File:** {questions_file}
- **JSON Data:** ../Fetch_data/unified_results.json
- **Generated:** {timestamp}

---

*Report generated by Agent Content Package - Batch Question Processor*
"""
    
    # Write to file
    try:
        output_path = Path("output_reports")
        output_path.mkdir(exist_ok=True)
        
        filepath = output_path / output_file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\n📄 Markdown report saved: {filepath}")
        print(f"📝 Report contains {len(markdown_content):,} characters")
        return str(filepath)
        
    except Exception as e:
        print(f"❌ Error saving markdown report: {str(e)}")
        return None


def main():
    """Main batch processing function."""
    
    print("🚀 Agent Content Package - Batch Question Processor")
    print("=" * 60)
    
    # Parse command line arguments
    questions_file = "questions"  # Default - now from agent_content folder
    output_prefix = "Batch_Questions_Report"  # Default
    
    if len(sys.argv) > 1:
        questions_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_prefix = sys.argv[2]
    
    # Generate timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_prefix}_{timestamp}.md"
    
    print(f"📁 Questions File: {questions_file}")
    print(f"📄 Output File: output_reports/{output_file}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Warning: GEMINI_API_KEY not found in environment")
        print("   Please set it with: export GEMINI_API_KEY='your_key_here'")
        return 1
    
    # Load questions
    questions = load_questions(questions_file)
    if not questions:
        print("❌ No valid questions found. Exiting.")
        return 1
    
    print(f"✅ Loaded {len(questions)} questions for processing")
    
    # Initialize the intelligent tool
    try:
        tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")
        print("✅ Intelligent Discovery and Synthesis Tool initialized")
    except Exception as e:
        print(f"❌ Error initializing tool: {str(e)}")
        return 1
    
    # Process all questions
    results = []
    start_batch_time = datetime.now()
    
    print(f"\n🔄 Processing {len(questions)} questions...")
    
    for i, question in enumerate(questions, 1):
        result = process_single_question(tool, question, i, len(questions))
        results.append(result)
    
    end_batch_time = datetime.now()
    total_batch_time = (end_batch_time - start_batch_time).total_seconds()
    
    # Generate summary
    successful = len([r for r in results if r['status'] == 'SUCCESS'])
    print(f"\n🎯 Batch Processing Complete!")
    print(f"📊 Results: {successful}/{len(questions)} successful ({(successful/len(questions)*100):.1f}%)")
    print(f"⏱️  Total Time: {total_batch_time:.2f} seconds")
    print(f"📈 Average: {total_batch_time/len(questions):.2f} seconds per question")
    
    # Generate markdown report
    print(f"\n📄 Generating comprehensive markdown report...")
    report_file = generate_markdown_report(results, questions_file, output_file)
    
    if report_file:
        print(f"✅ Batch processing completed successfully!")
        print(f"📋 Report saved: {report_file}")
        print(f"📊 Review the report for detailed answers and analysis")
    else:
        print(f"❌ Report generation failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())