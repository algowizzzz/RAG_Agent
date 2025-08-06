#!/usr/bin/env python3
"""
OSFI CAR Batch Analysis Tool
Processes a list of questions and generates comprehensive Markdown output 
with all reasoning steps and responses for documentation and analysis.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import io
from contextlib import redirect_stdout

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from osfi_car_enhanced_reasoning import EnhancedOSFICARAgent, ReasoningLogger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure osfi_car_enhanced_reasoning.py is in the same directory")
    sys.exit(1)

class BatchReasoningLogger(ReasoningLogger):
    """Enhanced logger that captures reasoning for Markdown output."""
    
    def __init__(self):
        super().__init__(show_reasoning=False)  # Don't display, just capture
        self.captured_output = []
    
    def log_step(self, step_type: str, description: str, details: Dict = None, thinking: str = None):
        """Override to ensure we capture all steps properly."""
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
        
        # Always capture for batch processing
        self._capture_step(log_entry)
    
    def _capture_step(self, log_entry: Dict):
        """Capture reasoning steps for batch output."""
        step_icons = {
            "decision": "🤔",
            "retrieval": "🔍", 
            "analysis": "🧠",
            "synthesis": "⚡",
            "tool_call": "🔧",
            "evaluation": "📊",
            "conclusion": "✅"
        }
        
        icon = step_icons.get(log_entry["type"], "💭")
        
        output = {
            "icon": icon,
            "step": log_entry["step"],
            "timestamp": log_entry["timestamp"],
            "type": log_entry["type"],
            "description": log_entry["description"],
            "thinking": log_entry["thinking"],
            "details": log_entry["details"]
        }
        
        self.captured_output.append(output)
    
    def _display_step(self, log_entry: Dict):
        """Override parent method to prevent display while still capturing."""
        # Don't display anything in batch mode, just capture
        pass
    
    def get_captured_reasoning(self) -> List[Dict]:
        """Get all captured reasoning steps."""
        return self.captured_output
    
    def clear_captured_reasoning(self):
        """Clear captured reasoning for next question."""
        self.captured_output = []
        self.session_log = []
        self.step_count = 0

class OSFIBatchAnalyzer:
    """Batch analyzer for OSFI CAR questions with Markdown output."""
    
    def __init__(self, pdf_directory: str, api_key: str = None):
        """
        Initialize the batch analyzer.
        
        Args:
            pdf_directory: Path to directory containing OSFI CAR PDF files
            api_key: Google API key for Gemini
        """
        self.pdf_directory = pdf_directory
        
        # Initialize agent with custom logger
        print("🔄 Initializing OSFI CAR Batch Analyzer...")
        self.agent = self._create_enhanced_agent(api_key)
        print("✅ Batch Analyzer ready!")
    
    def _create_enhanced_agent(self, api_key: str = None) -> EnhancedOSFICARAgent:
        """Create agent with batch-optimized logging."""
        
        # Set up API key
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            self._load_api_key_from_config()
        
        # Create agent with suppressed reasoning display
        agent = EnhancedOSFICARAgent(
            self.pdf_directory, 
            show_reasoning=False  # We'll capture it ourselves
        )
        
        # Replace the logger with our batch logger
        agent.reasoning_logger = BatchReasoningLogger()
        
        return agent
    
    def _load_api_key_from_config(self):
        """Load API key from config file."""
        config_path = os.path.join(os.path.dirname(__file__), "config")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith("api_key_gemini="):
                        api_key = line.split("=", 1)[1].strip()
                        os.environ["GOOGLE_API_KEY"] = api_key
                        return
        
        print("❌ Google API key not found!")
        print("Please either:")
        print("1. Set GOOGLE_API_KEY environment variable")
        print("2. Add 'api_key_gemini=YOUR_KEY' to config file")
        print("3. Pass API key as argument: --api-key YOUR_KEY")
        sys.exit(1)
    
    def process_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of questions and return detailed results.
        
        Args:
            questions: List of questions to process
            
        Returns:
            List of dictionaries containing question, reasoning, and response
        """
        results = []
        
        for i, question in enumerate(questions, 1):
            print(f"🔍 Processing question {i}/{len(questions)}: {question[:50]}...")
            
            # Clear previous reasoning
            self.agent.reasoning_logger.clear_captured_reasoning()
            self.agent.clear_history()
            
            try:
                # Get response
                response = self.agent.ask(question)
                
                # Get captured reasoning
                reasoning_steps = self.agent.reasoning_logger.get_captured_reasoning()
                
                # Get summary
                summary = self.agent.reasoning_logger.get_session_summary()
                
                result = {
                    "question": question,
                    "response": response,
                    "reasoning_steps": reasoning_steps,
                    "summary": summary,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "error": None
                }
                
            except Exception as e:
                result = {
                    "question": question,
                    "response": None,
                    "reasoning_steps": [],
                    "summary": {},
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                }
                print(f"❌ Error processing question: {e}")
            
            results.append(result)
        
        return results
    
    def generate_markdown_report(self, results: List[Dict[str, Any]], 
                                title: str = "OSFI CAR Analysis Report") -> str:
        """
        Generate comprehensive Markdown report.
        
        Args:
            results: Results from process_questions
            title: Report title
            
        Returns:
            Markdown formatted report
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md = f"""# {title}

*Generated on: {timestamp}*

---

## Executive Summary

- **Total Questions Processed:** {len(results)}
- **Successful Analyses:** {sum(1 for r in results if r['success'])}
- **Failed Analyses:** {sum(1 for r in results if not r['success'])}
- **Total Reasoning Steps:** {sum(r['summary'].get('total_steps', 0) for r in results if r['success'])}

---

## Analysis Results

"""

        for i, result in enumerate(results, 1):
            md += self._generate_question_section(i, result)
        
        # Add appendix
        md += self._generate_appendix(results)
        
        return md
    
    def _generate_question_section(self, question_num: int, result: Dict[str, Any]) -> str:
        """Generate Markdown section for a single question."""
        
        question = result['question']
        
        section = f"""### Question {question_num}

**Query:** *{question}*

"""
        
        if not result['success']:
            section += f"""**❌ Analysis Failed**

Error: {result['error']}

---

"""
            return section
        
        # Add reasoning process
        section += "#### 🧠 Agent Reasoning Process\n\n"
        
        reasoning_steps = result['reasoning_steps']
        if not reasoning_steps:
            section += "*No detailed reasoning steps captured. This may indicate a logging issue.*\n\n"
        else:
            for step in reasoning_steps:
                # More detailed step formatting
                section += f"**{step['icon']} Step {step['step']} ({step['timestamp']}) - {step['type'].title()}**\n\n"
                section += f"- **Action:** {step['description']}\n"
                
                if step['thinking']:
                    section += f"- **Reasoning:** {step['thinking']}\n"
                
                if step['details']:
                    section += "- **Details:**\n"
                    for key, value in step['details'].items():
                        if isinstance(value, list):
                            if len(value) <= 3:
                                value = ", ".join(str(v) for v in value)
                            else:
                                value = ", ".join(str(v) for v in value[:3]) + f" (and {len(value)-3} more)"
                        elif isinstance(value, str) and len(value) > 200:
                            value = value[:200] + "..."
                        section += f"  - {key.replace('_', ' ').title()}: {value}\n"
                
                section += "\n"
        
        # Add summary
        summary = result['summary']
        section += "#### 📊 Reasoning Summary\n\n"
        section += f"- **Total Steps:** {summary.get('total_steps', 0)}\n"
        section += f"- **Step Types:** {', '.join(set(summary.get('step_types', [])))}\n"
        section += f"- **Analysis Time:** {result['timestamp']}\n\n"
        
        # Add response
        section += "#### 🤖 Regulatory Guidance\n\n"
        response = result['response']
        section += f"{response}\n\n"
        
        section += "---\n\n"
        
        return section
    
    def _generate_appendix(self, results: List[Dict[str, Any]]) -> str:
        """Generate appendix with additional analysis."""
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return ""
        
        # Analyze reasoning patterns
        all_step_types = []
        total_steps = 0
        
        for result in successful_results:
            step_types = result['summary'].get('step_types', [])
            all_step_types.extend(step_types)
            total_steps += result['summary'].get('total_steps', 0)
        
        # Count step type frequency
        step_type_counts = {}
        for step_type in all_step_types:
            step_type_counts[step_type] = step_type_counts.get(step_type, 0) + 1
        
        appendix = f"""## Appendix: Analysis Patterns

### Reasoning Pattern Analysis

**Overall Statistics:**
- Average steps per question: {total_steps / len(successful_results):.1f}
- Most common reasoning type: {max(step_type_counts.items(), key=lambda x: x[1])[0] if step_type_counts else 'N/A'}

**Step Type Distribution:**
"""
        
        for step_type, count in sorted(step_type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(all_step_types)) * 100
            appendix += f"- **{step_type.title()}:** {count} occurrences ({percentage:.1f}%)\n"
        
        appendix += f"""

### Document Retrieval Analysis

**Questions requiring document retrieval:** {sum(1 for r in successful_results if any('retrieval' in step.get('type', '') for step in r.get('reasoning_steps', [])))}

**Questions answered without retrieval:** {sum(1 for r in successful_results if not any('retrieval' in step.get('type', '') for step in r.get('reasoning_steps', [])))}

---

*Report generated by OSFI CAR Batch Analysis Tool*
*Based on OSFI Capital Adequacy Ratio regulatory documents*
"""
        
        return appendix

def load_questions_from_file(filepath: str) -> List[str]:
    """Load questions from various file formats."""
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Questions file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Handle different formats
    if filepath.endswith('.json'):
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'questions' in data:
            return data['questions']
        else:
            raise ValueError("JSON file must contain a list of questions or a dict with 'questions' key")
    
    elif filepath.endswith('.txt'):
        # Split by lines, filter empty lines
        questions = [line.strip() for line in content.split('\n') if line.strip()]
        return questions
    
    else:
        raise ValueError("Unsupported file format. Use .txt or .json files.")

def main():
    """Main function for batch analysis."""
    
    parser = argparse.ArgumentParser(description="OSFI CAR Batch Analysis Tool")
    parser.add_argument("--questions", "-q", required=True,
                       help="Path to file containing questions (.txt or .json)")
    parser.add_argument("--output", "-o", default="osfi_car_analysis_report.md",
                       help="Output Markdown file path")
    parser.add_argument("--title", "-t", default="OSFI CAR Analysis Report",
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
        
        # Initialize analyzer
        analyzer = OSFIBatchAnalyzer(args.pdf_dir, args.api_key)
        
        # Process questions
        print(f"🔄 Processing {len(questions)} questions...")
        results = analyzer.process_questions(questions)
        
        # Generate report
        print(f"📝 Generating Markdown report...")
        report = analyzer.generate_markdown_report(results, args.title)
        
        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        total_steps = sum(r['summary'].get('total_steps', 0) for r in results if r['success'])
        
        print(f"\n✅ Analysis Complete!")
        print(f"📊 Results:")
        print(f"   - Questions processed: {len(questions)}")
        print(f"   - Successful analyses: {successful}")
        print(f"   - Total reasoning steps: {total_steps}")
        print(f"   - Report saved to: {args.output}")
        print(f"   - Report size: {len(report):,} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()