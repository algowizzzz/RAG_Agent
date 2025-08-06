#!/usr/bin/env python3
"""
OSFI CAR Batch Analysis Tool with Mathematical Scoring
Processes a list of questions and generates comprehensive Markdown output 
with all reasoning steps, responses, and quality scores for documentation and analysis.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import io
from contextlib import redirect_stdout

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try manual loading
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Map gemini_api_key to GOOGLE_API_KEY if available
if 'gemini_api_key' in os.environ and not os.environ.get('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.environ['gemini_api_key']

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from osfi_car_enhanced_reasoning_with_scoring import EnhancedOSFICARAgentWithScoring, ReasoningLogger, ResponseScorer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure osfi_car_enhanced_reasoning_with_scoring.py is in the same directory")
    sys.exit(1)

class BatchScoringLogger(ReasoningLogger):
    """Enhanced logger that captures reasoning and scoring for Markdown output."""
    
    def __init__(self):
        super().__init__(show_reasoning=False)  # Don't display, just capture
        self.captured_output = []
        self.scoring_results = []
    
    def log_step(self, step_type: str, description: str, details: Dict = None, thinking: str = None):
        """Override to ensure we capture all steps including scoring properly."""
        self.step_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            "step": self.step_count,
            "timestamp": timestamp,
            "type": step_type,
            "description": description,
            "details": details or {},
            "thinking": thinking
        }
        
        self.session_log.append(log_entry)
        
        # Capture scoring information separately for easy access
        if step_type == "scoring" and details:
            self.scoring_results.append({
                "timestamp": timestamp,
                "details": details,
                "thinking": thinking
            })
        
        # Always capture for batch processing
        self._capture_step(log_entry)
    
    def _capture_step(self, log_entry: Dict):
        """Capture step for Markdown formatting."""
        step_icons = {
            "decision": "🤔",
            "retrieval": "🔍", 
            "analysis": "🧠",
            "synthesis": "⚡",
            "tool_call": "🔧",
            "evaluation": "📊",
            "scoring": "🎯",
            "conclusion": "✅"
        }
        
        icon = step_icons.get(log_entry["type"], "💭")
        
        # Format the step
        step_text = f"\n{icon} **Agent Thinking Process [Step {log_entry['step']}]** ({log_entry['timestamp']})\n"
        step_text += f"   **Action:** {log_entry['description']}\n"
        
        if log_entry["thinking"]:
            step_text += f"   **Reasoning:** {log_entry['thinking']}\n"
        
        if log_entry["details"]:
            for key, value in log_entry["details"].items():
                if isinstance(value, dict):
                    # Special formatting for scoring details
                    if 'score' in key.lower() or 'relevance' in key.lower() or 'completeness' in key.lower():
                        formatted_scores = {}
                        for k, v in value.items():
                            if isinstance(v, float):
                                formatted_scores[k] = f"{v:.3f}"
                            else:
                                formatted_scores[k] = str(v)
                        step_text += f"   **{key.title().replace('_', ' ')}:** {formatted_scores}\n"
                    else:
                        step_text += f"   **{key.title().replace('_', ' ')}:** {value}\n"
                elif isinstance(value, str) and len(value) > 100:
                    step_text += f"   **{key.title().replace('_', ' ')}:** {value[:100]}...\n"
                else:
                    step_text += f"   **{key.title().replace('_', ' ')}:** {value}\n"
        
        self.captured_output.append(step_text)
    
    def get_captured_reasoning(self) -> str:
        """Get all captured reasoning as Markdown text."""
        return "".join(self.captured_output)
    
    def get_latest_scoring_results(self) -> Dict:
        """Get the most recent scoring results."""
        if self.scoring_results:
            return self.scoring_results[-1]
        return {}
    
    def clear_captured(self):
        """Clear captured output for next question."""
        self.captured_output = []
        self.scoring_results = []
        self.session_log = []
        self.step_count = 0

class OSFIBatchAnalyzerWithScoring:
    """Batch analyzer for OSFI CAR questions with mathematical scoring."""
    
    def __init__(self, pdf_directory: str = "osfi car", api_key: str = None):
        """Initialize the batch analyzer with scoring capabilities."""
        print("🔄 Initializing OSFI CAR Batch Analyzer with Mathematical Scoring...")
        
        # Create the enhanced agent with scoring
        self.agent = EnhancedOSFICARAgentWithScoring(
            pdf_directory=pdf_directory,
            api_key=api_key,
            show_reasoning=False  # We'll capture it through our logger
        )
        
        # Replace the agent's logger with our batch logger
        self.batch_logger = BatchScoringLogger()
        self.agent.reasoning_logger = self.batch_logger
        
        print("✅ Batch Analyzer with Scoring initialized!")
    
    def process_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Process a list of questions and return results with scoring."""
        results = []
        
        for i, question in enumerate(questions, 1):
            print(f"🔄 Processing question {i}/{len(questions)}: {question[:50]}...")
            
            try:
                # Clear previous reasoning
                self.batch_logger.clear_captured()
                
                # Process the question
                start_time = datetime.now()
                response = self.agent.ask(question)
                end_time = datetime.now()
                
                # Get captured reasoning and scoring
                captured_reasoning = self.batch_logger.get_captured_reasoning()
                scoring_results = self.batch_logger.get_latest_scoring_results()
                
                # Calculate processing time
                processing_time = (end_time - start_time).total_seconds()
                
                # Get reasoning summary
                summary = self.batch_logger.get_session_summary()
                
                result = {
                    'question': question,
                    'response': response,
                    'success': True,
                    'reasoning': captured_reasoning,
                    'scoring': scoring_results,
                    'processing_time': processing_time,
                    'timestamp': start_time.isoformat(),
                    'summary': summary
                }
                
                print(f"✅ Question {i} processed successfully")
                if scoring_results and 'details' in scoring_results:
                    details = scoring_results['details']
                    if 'overall_quality' in details:
                        quality = details['overall_quality']
                        grade = details.get('quality_grade', 'N/A')
                        print(f"   📊 Quality Score: {quality} - {grade}")
                
            except Exception as e:
                print(f"❌ Error processing question {i}: {e}")
                result = {
                    'question': question,
                    'response': None,
                    'success': False,
                    'error': str(e),
                    'reasoning': '',
                    'scoring': {},
                    'processing_time': 0,
                    'timestamp': datetime.now().isoformat(),
                    'summary': {'total_steps': 0, 'step_types': []}
                }
            
            results.append(result)
        
        return results
    
    def generate_markdown_report(self, results: List[Dict[str, Any]], title: str = "OSFI CAR Analysis Report") -> str:
        """Generate comprehensive Markdown report with scoring information."""
        
        # Calculate overall statistics
        successful = [r for r in results if r['success']]
        total_questions = len(results)
        successful_count = len(successful)
        total_steps = sum(r['summary'].get('total_steps', 0) for r in successful)
        avg_processing_time = sum(r['processing_time'] for r in successful) / len(successful) if successful else 0
        
        # Calculate scoring statistics
        scoring_stats = self._calculate_scoring_statistics(successful)
        
        # Generate report
        report = []
        
        # Header
        report.append(f"# {title}\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Analysis Tool:** OSFI CAR Enhanced Reasoning Agent with Mathematical Scoring\n\n")
        
        # Executive Summary with Scoring
        report.append("## 📊 Executive Summary\n")
        report.append(f"- **Total Questions Processed:** {total_questions}\n")
        report.append(f"- **Successful Analyses:** {successful_count}\n")
        report.append(f"- **Total Reasoning Steps:** {total_steps:,}\n")
        report.append(f"- **Average Processing Time:** {avg_processing_time:.2f} seconds\n")
        
        if scoring_stats:
            report.append("\n### 🎯 Quality Scoring Summary\n")
            report.append(f"- **Average Overall Quality:** {scoring_stats['avg_overall_quality']:.3f}/1.0\n")
            report.append(f"- **Average Relevance Score:** {scoring_stats['avg_relevance']:.3f}/1.0\n")
            report.append(f"- **Average Completeness Score:** {scoring_stats['avg_completeness']:.3f}/1.0\n")
            report.append(f"- **Quality Grade Distribution:**\n")
            for grade, count in scoring_stats['grade_distribution'].items():
                percentage = (count / successful_count) * 100
                report.append(f"  - {grade}: {count} ({percentage:.1f}%)\n")
        
        report.append("\n---\n\n")
        
        # Detailed Analysis for each question
        report.append("## 📋 Detailed Question Analysis\n\n")
        
        for i, result in enumerate(results, 1):
            report.append(f"### Question {i}\n\n")
            report.append(f"**Q:** {result['question']}\n\n")
            
            if result['success']:
                # Add scoring summary at the top
                if result['scoring'] and 'details' in result['scoring']:
                    scoring_details = result['scoring']['details']
                    report.append("#### 🎯 Quality Assessment\n\n")
                    
                    if 'overall_quality' in scoring_details:
                        quality = scoring_details['overall_quality']
                        grade = scoring_details.get('quality_grade', 'N/A')
                        report.append(f"**Overall Quality:** {quality} - {grade}\n\n")
                    
                    # Relevance breakdown
                    if 'relevance_scores' in scoring_details:
                        rel_scores = scoring_details['relevance_scores']
                        report.append("**Relevance Scores:**\n")
                        for key, value in rel_scores.items():
                            clean_key = key.replace('_', ' ').title()
                            if isinstance(value, str):
                                report.append(f"- {clean_key}: {value}\n")
                            else:
                                report.append(f"- {clean_key}: {value:.3f}\n")
                        report.append("\n")
                    
                    # Completeness breakdown
                    if 'completeness_scores' in scoring_details:
                        comp_scores = scoring_details['completeness_scores']
                        report.append("**Completeness Scores:**\n")
                        for key, value in comp_scores.items():
                            clean_key = key.replace('_', ' ').title()
                            if isinstance(value, str):
                                report.append(f"- {clean_key}: {value}\n")
                            else:
                                report.append(f"- {clean_key}: {value:.3f}\n")
                        report.append("\n")
                
                # Agent Response
                report.append("#### 🤖 Agent Response\n\n")
                report.append(f"{result['response']}\n\n")
                
                # Reasoning Process
                report.append("#### 🧠 Agent Reasoning Process\n\n")
                if result['reasoning']:
                    report.append(result['reasoning'])
                else:
                    report.append("*No detailed reasoning captured for this question.*\n")
                
                # Technical Details
                report.append("\n#### 📈 Technical Details\n\n")
                report.append(f"- **Processing Time:** {result['processing_time']:.2f} seconds\n")
                report.append(f"- **Reasoning Steps:** {result['summary'].get('total_steps', 0)}\n")
                report.append(f"- **Step Types:** {', '.join(set(result['summary'].get('step_types', [])))}\n")
                report.append(f"- **Timestamp:** {result['timestamp']}\n\n")
                
            else:
                report.append("#### ❌ Analysis Failed\n\n")
                report.append(f"**Error:** {result.get('error', 'Unknown error')}\n\n")
            
            report.append("---\n\n")
        
        # Appendix
        report.append("## 📖 Appendix\n\n")
        report.append("### Agent Configuration\n\n")
        report.append("- **Model:** Google Gemini 1.5 Pro\n")
        report.append("- **Reasoning Mode:** Enhanced with mathematical scoring\n")
        report.append("- **Document Retrieval:** Semantic search with quality scoring\n")
        report.append("- **Scoring System:** Relevance + Completeness assessment\n")
        report.append("- **Quality Grades:** A+ (Excellent) to C (Needs Improvement)\n\n")
        
        report.append("### Scoring Methodology\n\n")
        report.append("**Relevance Scoring:**\n")
        report.append("- Keyword Overlap: Question words found in response\n")
        report.append("- Context Usage: Utilization of retrieved documents\n")
        report.append("- Domain Relevance: Regulatory terminology density\n\n")
        
        report.append("**Completeness Scoring:**\n")
        report.append("- Information Density: Structured content and details\n")
        report.append("- Question Coverage: All parts of question addressed\n")
        report.append("- Reference Quality: Specific regulatory citations\n")
        report.append("- Explanation Depth: Explanatory phrases and reasoning\n\n")
        
        report.append("**Overall Quality = (Relevance × 0.5) + (Completeness × 0.5)**\n\n")
        
        report.append(f"---\n\n*Report generated by OSFI CAR Batch Analyzer with Mathematical Scoring v2.0*\n")
        
        return "".join(report)
    
    def _calculate_scoring_statistics(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from scoring results."""
        if not successful_results:
            return {}
        
        # Extract scoring data
        quality_scores = []
        relevance_scores = []
        completeness_scores = []
        grades = []
        
        for result in successful_results:
            if result['scoring'] and 'details' in result['scoring']:
                details = result['scoring']['details']
                
                if 'overall_quality' in details:
                    quality_scores.append(float(details['overall_quality']))
                
                if 'quality_grade' in details:
                    grades.append(details['quality_grade'])
                
                if 'relevance_scores' in details:
                    rel_scores = details['relevance_scores']
                    if 'overall_relevance' in rel_scores:
                        relevance_scores.append(float(rel_scores['overall_relevance']))
                
                if 'completeness_scores' in details:
                    comp_scores = details['completeness_scores']
                    if 'overall_completeness' in comp_scores:
                        completeness_scores.append(float(comp_scores['overall_completeness']))
        
        # Calculate averages
        stats = {}
        if quality_scores:
            stats['avg_overall_quality'] = sum(quality_scores) / len(quality_scores)
        if relevance_scores:
            stats['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
        if completeness_scores:
            stats['avg_completeness'] = sum(completeness_scores) / len(completeness_scores)
        
        # Grade distribution
        if grades:
            grade_dist = {}
            for grade in grades:
                grade_dist[grade] = grade_dist.get(grade, 0) + 1
            stats['grade_distribution'] = grade_dist
        
        return stats

def load_questions_from_file(file_path: str) -> List[str]:
    """Load questions from various file formats."""
    questions = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Questions file not found: {file_path}")
    
    # Determine file type and load accordingly
    _, ext = os.path.splitext(file_path.lower())
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if ext == '.json':
            # JSON format
            data = json.load(f)
            if isinstance(data, list):
                questions = [str(q) for q in data]
            elif isinstance(data, dict) and 'questions' in data:
                questions = [str(q) for q in data['questions']]
            else:
                raise ValueError("JSON file must contain a list of questions or a dict with 'questions' key")
        
        else:
            # Text format (one question per line)
            questions = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    if not questions:
        raise ValueError(f"No questions found in {file_path}")
    
    return questions

def main():
    """Main function for batch analysis with scoring."""
    parser = argparse.ArgumentParser(description="OSFI CAR Batch Analysis with Mathematical Scoring")
    parser.add_argument("questions", help="Path to questions file (JSON or text)")
    parser.add_argument("-o", "--output", default="full_reasoning_report_with_scoring.md",
                       help="Output Markdown file path")
    parser.add_argument("--title", "-t", default="OSFI CAR Analysis Report with Mathematical Scoring",
                       help="Report title")
    parser.add_argument("--pdf-dir", default="osfi car",
                       help="Directory containing OSFI CAR PDF files")
    parser.add_argument("--api-key", help="Google API key for Gemini")
    
    args = parser.parse_args()
    
    try:
        # Load questions
        print(f"📋 Loading questions from {args.questions}...")
        questions = load_questions_from_file(args.questions)
        print(f"✅ Loaded {len(questions)} questions")
        
        # Initialize analyzer with scoring
        analyzer = OSFIBatchAnalyzerWithScoring(args.pdf_dir, args.api_key)
        
        # Process questions
        print(f"🔄 Processing {len(questions)} questions with quality scoring...")
        results = analyzer.process_questions(questions)
        
        # Generate report
        print(f"📝 Generating Markdown report with scoring analysis...")
        report = analyzer.generate_markdown_report(results, args.title)
        
        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Summary with scoring statistics
        successful = sum(1 for r in results if r['success'])
        total_steps = sum(r['summary'].get('total_steps', 0) for r in results if r['success'])
        
        # Calculate quality statistics
        quality_scores = []
        for result in results:
            if result['success'] and result['scoring'] and 'details' in result['scoring']:
                details = result['scoring']['details']
                if 'overall_quality' in details:
                    quality_scores.append(float(details['overall_quality']))
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        print(f"\n✅ Analysis Complete!")
        print(f"📊 Results:")
        print(f"   - Questions processed: {len(questions)}")
        print(f"   - Successful analyses: {successful}")
        print(f"   - Total reasoning steps: {total_steps}")
        print(f"   - Average quality score: {avg_quality:.3f}/1.0")
        print(f"   - Report saved to: {args.output}")
        print(f"   - Report size: {len(report):,} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()