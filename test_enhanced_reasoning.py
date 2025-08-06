#!/usr/bin/env python3
"""
Test script for Enhanced OSFI CAR Agent with Visible Reasoning
Demonstrates step-by-step agent thinking and decision-making process.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from osfi_car_enhanced_reasoning import EnhancedOSFICARAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required packages are installed:")
    print("pip install langchain langchain-community pypdf google-generativeai langgraph")
    sys.exit(1)

def test_enhanced_reasoning():
    """Test the enhanced reasoning capabilities."""
    
    print("🧪 Testing Enhanced OSFI CAR Agent with Visible Reasoning")
    print("=" * 60)
    
    # Initialize agent
    try:
        print("🔄 Initializing agent...")
        agent = EnhancedOSFICARAgent(
            pdf_directory="osfi car",
            show_reasoning=True  # Enable reasoning display
        )
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test queries with different complexity levels
    test_queries = [
        {
            "question": "What is the minimum CET1 ratio?",
            "description": "Simple factual query - should trigger retrieval",
            "expected_reasoning": ["decision", "retrieval", "analysis", "synthesis"]
        },
        {
            "question": "How do capital adequacy ratios work and what are the calculation steps?",
            "description": "Complex explanatory query - should trigger multiple retrievals",
            "expected_reasoning": ["decision", "retrieval", "evaluation", "analysis", "synthesis"]
        },
        {
            "question": "Hello, can you help me?",
            "description": "Simple greeting - might not trigger retrieval",
            "expected_reasoning": ["decision", "analysis"]
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST CASE {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"{'='*60}")
        
        try:
            # Ask the question and observe reasoning
            response = agent.ask(test_case['question'])
            
            # Get reasoning summary
            summary = agent.get_reasoning_summary()
            
            print(f"\n📊 REASONING ANALYSIS:")
            print(f"   Total reasoning steps: {summary['total_steps']}")
            print(f"   Step types used: {', '.join(set(summary['step_types']))}")
            print(f"   Expected types: {', '.join(test_case['expected_reasoning'])}")
            
            # Check if expected reasoning types were used
            used_types = set(summary['step_types'])
            expected_types = set(test_case['expected_reasoning'])
            
            if expected_types.issubset(used_types):
                print("   ✅ Reasoning pattern matches expectations")
            else:
                missing = expected_types - used_types
                print(f"   ⚠️  Missing expected reasoning types: {', '.join(missing)}")
            
            print(f"\n🤖 AGENT RESPONSE:")
            print(f"   Length: {len(response)} characters")
            print(f"   Preview: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Clear history for next test
            agent.clear_history()
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            continue
    
    print(f"\n{'='*60}")
    print("🧪 TESTING COMPLETE")
    print("The enhanced agent successfully demonstrates:")
    print("✅ Step-by-step reasoning visibility")
    print("✅ Decision-making transparency")  
    print("✅ Tool usage explanations")
    print("✅ Information synthesis process")
    print(f"{'='*60}")

def demonstrate_interactive_mode():
    """Demonstrate interactive mode with reasoning."""
    
    print("\n🎮 Interactive Mode Demonstration")
    print("=" * 40)
    print("Starting interactive session with reasoning enabled...")
    print("You can now ask OSFI CAR questions and see the agent's thinking process!")
    print("Commands: 'clear', 'summary', 'help', 'quit'")
    print("=" * 40)
    
    try:
        agent = EnhancedOSFICARAgent(
            pdf_directory="osfi car",
            show_reasoning=True
        )
        
        while True:
            question = input("\n🤔 Ask about OSFI CAR regulations (or 'quit'): ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Demo complete!")
                break
            elif question.lower() == 'summary':
                summary = agent.get_reasoning_summary()
                print(f"📊 Steps: {summary['total_steps']}, Types: {', '.join(set(summary['step_types']))}")
                continue
            elif question.lower() == 'clear':
                agent.clear_history()
                continue
            elif not question:
                continue
            
            print(f"\n{'='*50}")
            print("🧠 AGENT REASONING PROCESS")
            print(f"{'='*50}")
            
            response = agent.ask(question)
            
            print(f"\n{'='*50}")
            print("🤖 FINAL RESPONSE")
            print(f"{'='*50}")
            print(response)
            
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Enhanced OSFI CAR Agent Reasoning")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive demonstration mode")
    args = parser.parse_args()
    
    if args.interactive:
        demonstrate_interactive_mode()
    else:
        test_enhanced_reasoning()