#!/usr/bin/env python3
"""
Enhanced OSFI CAR Interactive Chat Agent with Visible Reasoning
Shows all agent thinking, decision-making, and reasoning steps throughout the workflow.
"""

import os
import sys
import glob
import json
import time
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime

# Import required libraries
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.embeddings import init_embeddings
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain.tools.retriever import create_retriever_tool
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
    from langgraph.graph import END, START, StateGraph, MessagesState
    from typing_extensions import Literal
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install required packages:")
    print("pip install langchain langchain-community pypdf google-generativeai langgraph")
    sys.exit(1)

class ReasoningLogger:
    """Logs and displays agent reasoning steps."""
    
    def __init__(self, show_reasoning: bool = True):
        self.show_reasoning = show_reasoning
        self.step_count = 0
        self.session_log = []
    
    def log_step(self, step_type: str, description: str, details: Dict = None, thinking: str = None):
        """Log a reasoning step."""
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
        
        if self.show_reasoning:
            self._display_step(log_entry)
    
    def _display_step(self, log_entry: Dict):
        """Display a reasoning step to the user."""
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
        
        print(f"\n{icon} Agent Thinking Process [Step {log_entry['step']}] ({log_entry['timestamp']})")
        print(f"   Action: {log_entry['description']}")
        
        if log_entry["thinking"]:
            print(f"   Reasoning: {log_entry['thinking']}")
        
        if log_entry["details"]:
            for key, value in log_entry["details"].items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key.title()}: {value}")
    
    def get_session_summary(self):
        """Get summary of the reasoning session."""
        return {
            "total_steps": self.step_count,
            "step_types": [entry["type"] for entry in self.session_log],
            "session_log": self.session_log
        }

class EnhancedOSFICARAgent:
    """Interactive OSFI CAR regulatory compliance agent with visible reasoning."""
    
    def __init__(self, pdf_directory: str, api_key: str = None, show_reasoning: bool = True):
        """
        Initialize the Enhanced OSFI CAR agent.
        
        Args:
            pdf_directory: Path to directory containing OSFI CAR PDF files
            api_key: Google API key for Gemini (optional, reads from config if not provided)
            show_reasoning: Whether to display agent reasoning steps
        """
        self.pdf_directory = pdf_directory
        self.conversation_history = []
        self.reasoning_logger = ReasoningLogger(show_reasoning)
        
        # Set up API key
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            self._load_api_key_from_config()
        
        # Initialize components
        print("🔄 Initializing Enhanced OSFI CAR Agent with Reasoning...")
        self._load_documents()
        self._create_vectorstore()
        self._setup_agent()
        print("✅ Enhanced OSFI CAR Agent ready!")
    
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
    
    def _load_documents(self):
        """Load and process PDF documents."""
        self.reasoning_logger.log_step(
            "analysis", 
            "Loading OSFI CAR regulatory documents",
            thinking="Need to load all available PDF documents to build knowledge base for regulatory queries"
        )
        
        # Find PDF files
        pdf_pattern = os.path.join(self.pdf_directory, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            print(f"❌ No PDF files found in {self.pdf_directory}")
            sys.exit(1)
        
        self.reasoning_logger.log_step(
            "analysis",
            f"Found {len(pdf_files)} regulatory documents to process",
            details={"files": [os.path.basename(f) for f in pdf_files]},
            thinking="Multiple documents provide comprehensive regulatory coverage"
        )
        
        # Load documents
        self.documents = []
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(pdf_file)
                docs = loader.load()
                # Add source metadata
                for doc in docs:
                    doc.metadata['source_file'] = os.path.basename(pdf_file)
                self.documents.extend(docs)
            except Exception as e:
                print(f"⚠️  Warning: Could not load {pdf_file}: {e}")
        
        self.reasoning_logger.log_step(
            "analysis",
            f"Successfully loaded {len(self.documents)} pages of regulatory content",
            details={"total_pages": len(self.documents)},
            thinking="Rich document corpus enables comprehensive regulatory guidance"
        )
    
    def _create_vectorstore(self):
        """Create vector store from documents."""
        self.reasoning_logger.log_step(
            "analysis",
            "Creating semantic search infrastructure",
            thinking="Vector embeddings will enable intelligent retrieval of relevant regulatory content"
        )
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=2000,
            chunk_overlap=100
        )
        self.doc_splits = text_splitter.split_documents(self.documents)
        
        self.reasoning_logger.log_step(
            "analysis",
            f"Chunked documents into {len(self.doc_splits)} searchable segments",
            details={
                "chunk_size": 2000,
                "overlap": 100,
                "total_chunks": len(self.doc_splits)
            },
            thinking="Proper chunking ensures regulatory concepts stay together while enabling precise retrieval"
        )
        
        # Create embeddings and vector store
        try:
            embeddings = init_embeddings("openai:text-embedding-3-small")
            embedding_model = "OpenAI text-embedding-3-small"
        except Exception as e:
            print("⚠️  Warning: OpenAI embeddings not available, using HuggingFace embeddings")
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                print("Installing langchain-huggingface...")
                import subprocess
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'langchain-huggingface'])
                from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            embedding_model = "HuggingFace all-MiniLM-L6-v2"
        
        self.vectorstore = InMemoryVectorStore.from_documents(
            documents=self.doc_splits,
            embedding=embeddings
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 6})
        
        self.reasoning_logger.log_step(
            "analysis",
            "Vector search system ready for regulatory queries",
            details={
                "embedding_model": embedding_model,
                "retrieval_chunks": 6,
                "vectorstore_type": "InMemoryVectorStore"
            },
            thinking="Semantic search will find most relevant regulatory sections for each query"
        )
        
        # Create retriever tool
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "retrieve_osfi_car_docs",
            "Search and return information from OSFI Capital Adequacy Ratio (CAR) regulatory documents, including Basel III reforms and guidelines.",
        )
    
    def _setup_agent(self):
        """Set up the LangGraph agent."""
        self.reasoning_logger.log_step(
            "analysis",
            "Configuring intelligent regulatory agent",
            thinking="Gemini 1.5 Pro provides strong reasoning capabilities for complex regulatory analysis"
        )
        
        # Initialize LLM
        self.llm = init_chat_model("gemini-1.5-pro", model_provider="google_genai", temperature=0)
        self.tools = [self.retriever_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Enhanced system prompt with reasoning instructions
        self.system_prompt = """You are a specialized regulatory compliance assistant focused on OSFI (Office of the Superintendent of Financial Institutions) Capital Adequacy Ratio (CAR) requirements and Basel III reforms.

Your expertise includes:
- Capital adequacy calculations and minimum requirements
- Risk-weighted assets (RWA) calculations
- Basel III framework implementation in Canada
- OSFI regulatory guidelines and requirements
- Tier 1 and Tier 2 capital definitions and calculations
- Credit risk, market risk, and operational risk capital requirements

IMPORTANT: You must think through your response process step by step:

When answering questions:
1. FIRST: Analyze the question to understand what regulatory information is needed
2. THEN: Retrieve relevant context from the OSFI CAR documents before responding
3. NEXT: Evaluate the retrieved information for completeness and relevance
4. FINALLY: Synthesize a comprehensive response with specific regulatory references

For each step, explain your reasoning process. Always:
- Provide specific regulatory references when possible (chapter, section, paragraph)
- Explain complex regulatory concepts clearly
- Include relevant calculation methods or formulas when applicable
- Indicate if additional professional advice may be needed for implementation
- Show your decision-making process for tool usage

Use your retrieval tool to gather comprehensive context before providing detailed regulatory guidance."""
        
        # Build workflow
        builder = StateGraph(MessagesState)
        builder.add_node("llm_call", self._enhanced_llm_call)
        builder.add_node("tool_node", self._enhanced_tool_node)
        
        builder.add_edge(START, "llm_call")
        builder.add_conditional_edges(
            "llm_call",
            self._enhanced_should_continue,
            {
                "tool_node": "tool_node",
                END: END,
            },
        )
        builder.add_edge("tool_node", "llm_call")
        
        self.agent = builder.compile()
        
        self.reasoning_logger.log_step(
            "analysis",
            "Agent workflow configured with reasoning transparency",
            details={
                "llm_model": "Gemini 1.5 Pro",
                "workflow_nodes": ["llm_call", "tool_node"],
                "reasoning_enabled": True
            },
            thinking="LangGraph workflow enables transparent decision-making and tool usage"
        )
    
    def _enhanced_llm_call(self, state: MessagesState) -> Dict[str, Any]:
        """Enhanced LLM call with reasoning logging."""
        self.reasoning_logger.log_step(
            "decision",
            "Evaluating user query and determining response strategy",
            thinking="Need to analyze the question complexity and decide whether regulatory document retrieval is necessary"
        )
        
        # Get the user's latest message
        user_message = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'type') and msg.type == 'human':
                user_message = msg.content
                break
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                user_message = msg.get('content')
                break
        
        if user_message:
            self.reasoning_logger.log_step(
                "analysis",
                "Analyzing user query for regulatory scope and complexity",
                details={"query": user_message[:200] + "..." if len(user_message) > 200 else user_message},
                thinking="Understanding query type helps determine retrieval strategy and response approach"
            )
        
        result = self.llm_with_tools.invoke(
            [SystemMessage(content=self.system_prompt)] + state["messages"]
        )
        
        # Log the LLM's decision
        has_tool_calls = hasattr(result, 'tool_calls') and result.tool_calls
        self.reasoning_logger.log_step(
            "decision",
            f"LLM decided to {'use retrieval tools' if has_tool_calls else 'respond directly'}",
            details={
                "tool_calls_made": len(result.tool_calls) if has_tool_calls else 0,
                "response_length": len(result.content) if hasattr(result, 'content') else 0
            },
            thinking=f"{'Complex query requires regulatory document retrieval' if has_tool_calls else 'Simple query can be answered with existing knowledge'}"
        )
        
        return {"messages": [result]}
    
    def _enhanced_tool_node(self, state: MessagesState) -> Dict[str, Any]:
        """Enhanced tool execution with reasoning logging."""
        tool_calls = state["messages"][-1].tool_calls
        
        self.reasoning_logger.log_step(
            "tool_call",
            f"Executing {len(tool_calls)} retrieval operation(s)",
            thinking="Searching regulatory documents for relevant information to provide accurate guidance"
        )
        
        result = []
        for i, tool_call in enumerate(tool_calls):
            tool = self.tools_by_name[tool_call["name"]]
            query = tool_call["args"].get("query", "")
            
            self.reasoning_logger.log_step(
                "retrieval",
                f"Searching OSFI documents for: '{query}'",
                details={
                    "search_query": query,
                    "tool_name": tool_call["name"],
                    "call_index": i+1
                },
                thinking="Semantic search will find most relevant regulatory sections for this specific query"
            )
            
            # Execute tool and time it
            start_time = time.time()
            observation = tool.invoke(tool_call["args"])
            end_time = time.time()
            
            # Analyze retrieved content
            content_length = len(observation)
            word_count = len(observation.split())
            
            self.reasoning_logger.log_step(
                "evaluation",
                f"Retrieved {word_count} words of regulatory content",
                details={
                    "content_length": content_length,
                    "word_count": word_count,
                    "retrieval_time": f"{end_time - start_time:.2f}s",
                    "relevant_sections": "Multiple regulatory sections found"
                },
                thinking="Retrieved content provides comprehensive regulatory context for accurate response"
            )
            
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        
        return {"messages": result}
    
    def _enhanced_should_continue(self, state: MessagesState) -> Literal["tool_node", "__end__"]:
        """Enhanced decision logic with reasoning logging."""
        messages = state["messages"]
        last_message = messages[-1]
        
        has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
        
        if has_tool_calls:
            self.reasoning_logger.log_step(
                "decision",
                "Proceeding to retrieve regulatory documents",
                details={"tool_calls_count": len(last_message.tool_calls)},
                thinking="Agent determined that document retrieval is necessary to provide accurate regulatory guidance"
            )
            return "tool_node"
        else:
            self.reasoning_logger.log_step(
                "conclusion",
                "Sufficient information available to provide final response",
                thinking="Agent has enough context (either from retrieval or existing knowledge) to provide comprehensive answer"
            )
            return END
    
    def ask(self, question: str) -> str:
        """
        Ask the agent a question with full reasoning visibility.
        
        Args:
            question: User question about OSFI CAR regulations
            
        Returns:
            Agent response
        """
        # Reset step counter for new question
        self.reasoning_logger.step_count = 0
        
        self.reasoning_logger.log_step(
            "analysis",
            "Processing new regulatory query",
            details={"question": question},
            thinking="Starting comprehensive analysis to provide accurate regulatory guidance"
        )
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Get agent response
        self.reasoning_logger.log_step(
            "analysis",
            "Initiating agent workflow",
            thinking="Passing query through reasoning workflow to determine optimal response strategy"
        )
        
        result = self.agent.invoke({"messages": self.conversation_history})
        
        # Extract response and update history
        response = result['messages'][-1].content
        self.conversation_history = result['messages']
        
        self.reasoning_logger.log_step(
            "synthesis",
            "Final response synthesized",
            details={
                "response_length": len(response),
                "total_reasoning_steps": self.reasoning_logger.step_count
            },
            thinking="Combined retrieved regulatory information with analysis to provide comprehensive guidance"
        )
        
        return response
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.reasoning_logger.session_log = []
        self.reasoning_logger.step_count = 0
        print("🗑️  Conversation history and reasoning log cleared")
    
    def get_reasoning_summary(self):
        """Get summary of reasoning process."""
        return self.reasoning_logger.get_session_summary()

def print_welcome():
    """Print welcome message."""
    print("=" * 70)
    print("🏛️  Enhanced OSFI CAR Interactive Regulatory Assistant")
    print("🧠  With Visible Agent Reasoning & Decision-Making")
    print("=" * 70)
    print("Ask questions about:")
    print("• Capital adequacy requirements")
    print("• Basel III implementation")
    print("• Risk-weighted asset calculations")
    print("• OSFI regulatory guidelines")
    print("• Tier 1 and Tier 2 capital definitions")
    print()
    print("💭 The agent will show you its thinking process:")
    print("• Decision-making steps")
    print("• Document retrieval reasoning")
    print("• Information synthesis process")
    print()
    print("Commands:")
    print("• Type your question and press Enter")
    print("• 'clear' - Clear conversation history")
    print("• 'summary' - Show reasoning summary")
    print("• 'help' - Show this help message") 
    print("• 'quit' or 'exit' - Exit the program")
    print("=" * 70)

def print_help():
    """Print help message."""
    print("\n📖 Help:")
    print("This enhanced agent shows its reasoning process while answering OSFI CAR questions.")
    print("\nExample questions:")
    print("• What is the minimum Common Equity Tier 1 capital ratio?")
    print("• How do you calculate risk-weighted assets for credit risk?")
    print("• What are the components of Tier 1 capital?")
    print("• What are the Basel III leverage ratio requirements?")
    print("• Explain the capital conservation buffer")
    print("\n🧠 Watch for reasoning indicators:")
    print("🤔 Decision-making")
    print("🔍 Document retrieval")
    print("🧠 Analysis")
    print("⚡ Information synthesis")
    print("✅ Conclusion")
    print()

def main():
    """Main interactive loop."""
    parser = argparse.ArgumentParser(description="Enhanced OSFI CAR Interactive Agent with Reasoning")
    parser.add_argument("--pdf-dir", default="osfi car", 
                       help="Directory containing OSFI CAR PDF files")
    parser.add_argument("--api-key", help="Google API key for Gemini")
    parser.add_argument("--no-reasoning", action="store_true", 
                       help="Disable reasoning display")
    args = parser.parse_args()
    
    # Initialize agent
    try:
        agent = EnhancedOSFICARAgent(
            args.pdf_dir, 
            args.api_key, 
            show_reasoning=not args.no_reasoning
        )
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Print welcome
    print_welcome()
    
    # Interactive loop
    while True:
        try:
            # Get user input
            question = input("\n🤔 Ask me about OSFI CAR regulations: ").strip()
            
            # Handle commands
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif question.lower() == 'clear':
                agent.clear_history()
                continue
            elif question.lower() == 'summary':
                summary = agent.get_reasoning_summary()
                print(f"\n📊 Reasoning Summary:")
                print(f"   Total steps: {summary['total_steps']}")
                print(f"   Step types: {', '.join(set(summary['step_types']))}")
                continue
            elif question.lower() == 'help':
                print_help()
                continue
            elif not question:
                continue
            
            # Get response with reasoning
            print(f"\n{'='*50}")
            print("🧠 AGENT REASONING PROCESS")
            print(f"{'='*50}")
            
            response = agent.ask(question)
            
            # Display response
            print(f"\n{'='*50}")
            print("🤖 FINAL REGULATORY GUIDANCE")
            print(f"{'='*50}")
            print(response)
            print(f"{'='*50}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()