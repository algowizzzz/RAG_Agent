#!/usr/bin/env python3
"""
OSFI CAR Interactive Chat Agent
Interactive terminal-based RAG agent for OSFI Capital Adequacy Ratio documents.
"""

import os
import sys
import glob
from typing import List, Dict, Any, Optional
import argparse

# Import required libraries
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.embeddings import init_embeddings
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain.tools.retriever import create_retriever_tool
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import SystemMessage, ToolMessage
    from langgraph.graph import END, START, StateGraph, MessagesState
    from typing_extensions import Literal
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install required packages:")
    print("pip install langchain langchain-community pypdf google-generativeai langgraph")
    sys.exit(1)

class OSFICARAgent:
    """Interactive OSFI CAR regulatory compliance agent."""
    
    def __init__(self, pdf_directory: str, api_key: str = None):
        """
        Initialize the OSFI CAR agent.
        
        Args:
            pdf_directory: Path to directory containing OSFI CAR PDF files
            api_key: Google API key for Gemini (optional, reads from config if not provided)
        """
        self.pdf_directory = pdf_directory
        self.conversation_history = []
        
        # Set up API key
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            self._load_api_key_from_config()
        
        # Initialize components
        print("🔄 Initializing OSFI CAR Agent...")
        self._load_documents()
        self._create_vectorstore()
        self._setup_agent()
        print("✅ OSFI CAR Agent ready!")
    
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
        print("📄 Loading OSFI CAR documents...")
        
        # Find PDF files
        pdf_pattern = os.path.join(self.pdf_directory, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            print(f"❌ No PDF files found in {self.pdf_directory}")
            sys.exit(1)
        
        print(f"📚 Found {len(pdf_files)} PDF files:")
        for pdf_file in pdf_files:
            print(f"   - {os.path.basename(pdf_file)}")
        
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
        
        print(f"📖 Loaded {len(self.documents)} pages total")
    
    def _create_vectorstore(self):
        """Create vector store from documents."""
        print("🔍 Creating vector embeddings...")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=2000,
            chunk_overlap=100
        )
        self.doc_splits = text_splitter.split_documents(self.documents)
        print(f"📑 Created {len(self.doc_splits)} document chunks")
        
        # Create embeddings and vector store
        try:
            embeddings = init_embeddings("openai:text-embedding-3-small")
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
        self.vectorstore = InMemoryVectorStore.from_documents(
            documents=self.doc_splits,
            embedding=embeddings
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 6})
        
        # Create retriever tool
        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "retrieve_osfi_car_docs",
            "Search and return information from OSFI Capital Adequacy Ratio (CAR) regulatory documents, including Basel III reforms and guidelines.",
        )
    
    def _setup_agent(self):
        """Set up the LangGraph agent."""
        print("🤖 Setting up Gemini agent...")
        
        # Initialize LLM
        self.llm = init_chat_model("gemini-1.5-pro", model_provider="google_genai", temperature=0)
        self.tools = [self.retriever_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt
        self.system_prompt = """You are a specialized regulatory compliance assistant focused on OSFI (Office of the Superintendent of Financial Institutions) Capital Adequacy Ratio (CAR) requirements and Basel III reforms.

Your expertise includes:
- Capital adequacy calculations and minimum requirements
- Risk-weighted assets (RWA) calculations
- Basel III framework implementation in Canada
- OSFI regulatory guidelines and requirements
- Tier 1 and Tier 2 capital definitions and calculations
- Credit risk, market risk, and operational risk capital requirements

When answering questions:
1. Always retrieve relevant context from the OSFI CAR documents before responding
2. Provide specific regulatory references when possible (chapter, section, paragraph)
3. Explain complex regulatory concepts clearly
4. Include relevant calculation methods or formulas when applicable
5. Indicate if additional professional advice may be needed for implementation

Use your retrieval tool to gather comprehensive context before providing detailed regulatory guidance."""
        
        # Build workflow
        builder = StateGraph(MessagesState)
        builder.add_node("llm_call", self._llm_call)
        builder.add_node("tool_node", self._tool_node)
        
        builder.add_edge(START, "llm_call")
        builder.add_conditional_edges(
            "llm_call",
            self._should_continue,
            {
                "tool_node": "tool_node",
                END: END,
            },
        )
        builder.add_edge("tool_node", "llm_call")
        
        self.agent = builder.compile()
    
    def _llm_call(self, state: MessagesState) -> Dict[str, Any]:
        """LLM call with system prompt."""
        return {
            "messages": [
                self.llm_with_tools.invoke(
                    [SystemMessage(content=self.system_prompt)] + state["messages"]
                )
            ]
        }
    
    def _tool_node(self, state: MessagesState) -> Dict[str, Any]:
        """Execute tools."""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = self.tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}
    
    def _should_continue(self, state: MessagesState) -> Literal["tool_node", "__end__"]:
        """Decide whether to continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tool_node"
        return END
    
    def ask(self, question: str) -> str:
        """
        Ask the agent a question.
        
        Args:
            question: User question about OSFI CAR regulations
            
        Returns:
            Agent response
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Get agent response
        result = self.agent.invoke({"messages": self.conversation_history})
        
        # Extract response and update history
        response = result['messages'][-1].content
        self.conversation_history = result['messages']
        
        return response
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("🗑️  Conversation history cleared")

def print_welcome():
    """Print welcome message."""
    print("=" * 60)
    print("🏛️  OSFI CAR Interactive Regulatory Assistant")
    print("=" * 60)
    print("Ask questions about:")
    print("• Capital adequacy requirements")
    print("• Basel III implementation")
    print("• Risk-weighted asset calculations")
    print("• OSFI regulatory guidelines")
    print("• Tier 1 and Tier 2 capital definitions")
    print()
    print("Commands:")
    print("• Type your question and press Enter")
    print("• 'clear' - Clear conversation history")
    print("• 'help' - Show this help message")
    print("• 'quit' or 'exit' - Exit the program")
    print("=" * 60)

def print_help():
    """Print help message."""
    print("\n📖 Help:")
    print("This agent can answer questions about OSFI CAR regulations.")
    print("\nExample questions:")
    print("• What is the minimum Common Equity Tier 1 capital ratio?")
    print("• How do you calculate risk-weighted assets for credit risk?")
    print("• What are the components of Tier 1 capital?")
    print("• What are the Basel III leverage ratio requirements?")
    print("• Explain the capital conservation buffer")
    print()

def main():
    """Main interactive loop."""
    parser = argparse.ArgumentParser(description="OSFI CAR Interactive Agent")
    parser.add_argument("--pdf-dir", default="osfi car", 
                       help="Directory containing OSFI CAR PDF files")
    parser.add_argument("--api-key", help="Google API key for Gemini")
    args = parser.parse_args()
    
    # Initialize agent
    try:
        agent = OSFICARAgent(args.pdf_dir, args.api_key)
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
            elif question.lower() == 'help':
                print_help()
                continue
            elif not question:
                continue
            
            # Get response
            print("\n🔍 Searching OSFI documents...")
            response = agent.ask(question)
            
            # Display response
            print("\n🤖 OSFI CAR Agent Response:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()