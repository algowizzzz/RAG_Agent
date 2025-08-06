#!/usr/bin/env python3
"""
Enhanced OSFI CAR Interactive Chat Agent with Visible Reasoning and Mathematical Scoring
Shows all agent thinking, decision-making, reasoning steps, and mathematical quality scores.
"""

import os
import sys
import glob
import json
import time
import re
import math
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
    from typing_extensions import Literal, TypedDict
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install required packages:")
    print("pip install langchain langchain-community pypdf google-generativeai langgraph")
    sys.exit(1)

class EnhancedState(MessagesState):
    """Extended state that includes retrieved chunks for scoring."""
    retrieved_chunks: List[str]

class ResponseScorer:
    """Simple mathematical scoring system for response quality."""
    
    def __init__(self):
        self.regulatory_keywords = [
            'capital', 'adequacy', 'ratio', 'CAR', 'tier', 'leverage', 'risk', 'weighted', 
            'assets', 'RWA', 'basel', 'framework', 'OSFI', 'guideline', 'regulation',
            'calculate', 'formula', 'percentage', 'minimum', 'requirement', 'compliance'
        ]
    
    def score_relevance(self, question: str, response: str, retrieved_chunks: List[str] = None) -> Dict[str, float]:
        """Calculate relevance scores."""
        scores = {}
        
        # 1. Keyword overlap score
        scores['keyword_overlap'] = self._keyword_overlap(question, response)
        
        # 2. Domain relevance score
        scores['domain_relevance'] = self._domain_relevance(response)
        
        # 3. NEW: Citation-based relevance (proxy for context usage)
        scores['citation_relevance'] = self._citation_relevance(response)
        
        # Combined relevance (weighted average)
        weights = {'keyword_overlap': 0.4, 'domain_relevance': 0.4, 'citation_relevance': 0.2}
        scores['overall_relevance'] = sum(scores[key] * weights[key] for key in weights)
        
        return scores
    
    def score_completeness(self, question: str, response: str) -> Dict[str, float]:
        """Calculate completeness scores."""
        scores = {}
        
        # 1. Information density
        scores['info_density'] = self._info_density(response)
        
        # 2. Question coverage  
        scores['question_coverage'] = self._question_coverage(question, response)
        
        # 3. Reference quality
        scores['reference_quality'] = self._reference_quality(response)
        
        # 4. Explanation depth
        scores['explanation_depth'] = self._explanation_depth(response)
        
        # Combined completeness (weighted average)
        weights = {'info_density': 0.2, 'question_coverage': 0.3, 
                  'reference_quality': 0.3, 'explanation_depth': 0.2}
        scores['overall_completeness'] = sum(scores[key] * weights[key] for key in weights)
        
        return scores
    
    def _keyword_overlap(self, question: str, response: str) -> float:
        """Calculate keyword overlap between question and response."""
        q_words = set(re.findall(r'\b\w+\b', question.lower()))
        r_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 'where', 'why'}
        q_words -= stop_words
        
        if not q_words:
            return 1.0
        
        overlap = len(q_words.intersection(r_words)) / len(q_words)
        return min(1.0, overlap)
    
    def _context_usage(self, retrieved_chunks: List[str], response: str) -> float:
        """Calculate how well response uses retrieved context."""
        if not retrieved_chunks:
            return 0.0
        
        context_text = ' '.join(retrieved_chunks)
        
        # Extract key phrases and terms (3+ chars, filter common words)
        context_words = set(re.findall(r'\b\w{3,}\b', context_text.lower()))
        response_words = set(re.findall(r'\b\w{3,}\b', response.lower()))
        
        # Remove very common words that don't indicate context usage
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'then', 'them', 'each', 'which', 'their', 'time', 'will', 'about', 'there', 'been', 'many', 'than', 'into', 'very', 'what', 'know', 'just', 'first', 'get', 'over', 'think', 'also', 'back', 'after', 'work', 'life', 'only', 'year', 'come', 'its', 'state', 'much', 'take', 'years', 'good', 'way', 'well', 'man', 'even', 'most', 'made', 'should', 'still', 'being', 'now', 'against', 'during', 'where', 'when', 'why', 'how', 'any', 'some', 'these', 'those', 'other', 'more', 'such', 'through', 'before', 'after'}
        context_words -= common_words
        
        if not context_words:
            return 0.0
        
        # Calculate overlap
        overlap = context_words.intersection(response_words)
        usage = len(overlap) / len(context_words)
        
        # Boost for good usage, but cap at 1.0
        return min(1.0, usage * 1.2)
    
    def _citation_relevance(self, response: str) -> float:
        """Calculate relevance based on specific regulatory citations (proxy for context usage)."""
        # Look for specific regulatory citations that indicate document usage
        citation_patterns = [
            r'\b(chapter|section|paragraph)\s+[\d\.]+', # Chapter 1, Section 2.3, etc.
            r'\btable\s+\d+', # Table 1, Table 2, etc.
            r'\b(basel|osfi)\s+(iii|car|guideline)', # Basel III, OSFI CAR, etc.
            r'\b(cat(egory)?\s+[iv]+|d-sibs?)', # Category I, D-SIBs, etc.
            r'\brisk[- ]weighted\s+assets?', # Risk-weighted assets
            r'\bcapital\s+(adequacy|conservation|requirement)', # Capital adequacy, etc.
        ]
        
        citation_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                           for pattern in citation_patterns)
        
        # Normalize by response length (citations per 100 words)
        words = len(response.split())
        if words == 0:
            return 0.0
        
        citation_density = citation_count / (words / 100)
        
        # Cap at 1.0 and provide reasonable scaling
        return min(1.0, citation_density * 0.3)
    
    def _domain_relevance(self, response: str) -> float:
        """Calculate regulatory domain relevance."""
        response_lower = response.lower()
        found_keywords = sum(1 for keyword in self.regulatory_keywords 
                           if keyword.lower() in response_lower)
        
        # Score based on keyword density
        max_expected = min(10, len(self.regulatory_keywords))  # Don't expect all keywords
        return min(1.0, found_keywords / max_expected)
    
    def _info_density(self, response: str) -> float:
        """Calculate information density."""
        words = response.split()
        if len(words) < 10:
            return 0.3  # Too short
        
        # Look for structured information
        has_numbers = bool(re.search(r'\d+%|\d+\.\d+', response))
        has_lists = bool(re.search(r'[•\-\*]\s|^\d+\.', response, re.MULTILINE))
        has_structure = bool(re.search(r'(chapter|section|paragraph)', response, re.IGNORECASE))
        
        # Base score from length
        length_score = min(1.0, len(words) / 150)  # Optimal around 150 words
        structure_score = (has_numbers + has_lists + has_structure) / 3
        
        return (length_score * 0.6 + structure_score * 0.4)
    
    def _question_coverage(self, question: str, response: str) -> float:
        """Calculate how well response covers the question."""
        # Simple approach: check if question words appear in response
        q_words = set(re.findall(r'\b\w{3,}\b', question.lower()))
        r_words = set(re.findall(r'\b\w{3,}\b', response.lower()))
        
        # Remove stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'who', 'oil', 'sit', 'set'}
        q_words -= stop_words
        
        if not q_words:
            return 1.0
        
        coverage = len(q_words.intersection(r_words)) / len(q_words)
        return min(1.0, coverage)
    
    def _reference_quality(self, response: str) -> float:
        """Calculate quality of regulatory references."""
        # Count specific references
        specific_refs = len(re.findall(r'\b(chapter|section|paragraph)\s+[\d\.]+', response, re.IGNORECASE))
        general_refs = len(re.findall(r'\b(OSFI|Basel|CAR|guideline|regulation)', response, re.IGNORECASE))
        
        specific_score = min(1.0, specific_refs * 0.4)
        general_score = min(0.6, general_refs * 0.15)
        
        # Cap total at 1.0 to ensure scores don't exceed maximum
        return min(1.0, specific_score + general_score)
    
    def _explanation_depth(self, response: str) -> float:
        """Calculate depth of explanation."""
        # Expanded explanatory patterns
        explanatory_patterns = [
            # Causal explanations
            r'\bbecause\b', r'\bdue\s+to\b', r'\bas\s+a\s+result\b', r'\btherefore\b', r'\bconsequently\b',
            r'\bsince\b', r'\bgiven\s+that\b', r'\bin\s+order\s+to\b', r'\bso\s+that\b',
            
            # Clarifying explanations
            r'\bthis\s+means\b', r'\bin\s+other\s+words\b', r'\bspecifically\b', r'\bthat\s+is\b',
            r'\bnamely\b', r'\bto\s+clarify\b', r'\bto\s+explain\b', r'\bin\s+essence\b',
            
            # Examples and illustrations
            r'\bfor\s+example\b', r'\bfor\s+instance\b', r'\bsuch\s+as\b', r'\bincluding\b',
            r'\bto\s+illustrate\b', r'\bas\s+shown\b', r'\bas\s+follows\b', r'\be\.g\.\b',
            
            # Definitions and descriptions
            r'\bis\s+defined\s+as\b', r'\brefers\s+to\b', r'\bmeans\s+that\b', r'\binvolves\b',
            r'\bconsists\s+of\b', r'\bcomprise[sd]?\s+of\b', r'\bentails\b',
            
            # Step-by-step indicators
            r'\bfirst\b', r'\bsecond\b', r'\bthird\b', r'\bnext\b', r'\bthen\b', r'\bfinally\b',
            r'\bstep\s+\d+\b', r'\binitially\b', r'\bsubsequently\b',
            
            # Comparative explanations
            r'\bunlike\b', r'\bin\s+contrast\b', r'\bhowever\b', r'\bwhereas\b', r'\balthough\b',
            r'\bcompared\s+to\b', r'\bon\s+the\s+other\s+hand\b'
        ]
        
        explanation_count = sum(1 for pattern in explanatory_patterns 
                              if re.search(pattern, response, re.IGNORECASE))
        
        # Look for structured explanation indicators
        structure_indicators = [
            r'^\d+\.\s',  # Numbered lists
            r'^[•\-\*]\s',  # Bullet points
            r':\s*$',  # Colons at end of lines (often before explanations)
            r'\?$',  # Questions (rhetorical explanatory questions)
        ]
        
        structure_count = sum(1 for pattern in structure_indicators 
                            if re.search(pattern, response, re.MULTILINE))
        
        # Calculate explanation density with better normalization
        words = len(response.split())
        if words == 0:
            return 0.0
        
        # Score based on explanatory elements per 100 words (more reasonable baseline)
        explanation_density = explanation_count / (words / 100)
        structure_density = structure_count / (words / 200)  # Structure elements per 200 words
        
        # Combine scores with weights
        combined_score = (explanation_density * 0.7) + (structure_density * 0.3)
        
        # More generous scoring with cap at 1.0
        return min(1.0, combined_score * 0.5)
    
    def get_quality_grade(self, overall_score: float) -> str:
        """Convert score to letter grade."""
        if overall_score >= 0.9:
            return "A+ (Excellent)"
        elif overall_score >= 0.8:
            return "A (Very Good)"
        elif overall_score >= 0.7:
            return "B+ (Good)"
        elif overall_score >= 0.6:
            return "B (Satisfactory)"
        elif overall_score >= 0.5:
            return "C+ (Fair)"
        else:
            return "C (Needs Improvement)"

class ReasoningLogger:
    """Logs and displays agent reasoning steps with scoring."""
    
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
            "scoring": "🎯",
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
                elif isinstance(value, dict):
                    # Format scoring details nicely
                    if 'score' in key.lower() or 'relevance' in key.lower() or 'completeness' in key.lower():
                        value = {k: f"{v:.3f}" if isinstance(v, float) else v for k, v in value.items()}
                print(f"   {key.title().replace('_', ' ')}: {value}")
    
    def get_session_summary(self):
        """Get summary of the reasoning session."""
        return {
            "total_steps": self.step_count,
            "step_types": [entry["type"] for entry in self.session_log],
            "session_log": self.session_log
        }

class EnhancedOSFICARAgentWithScoring:
    """Interactive OSFI CAR regulatory compliance agent with visible reasoning and mathematical scoring."""
    
    def __init__(self, pdf_directory: str, api_key: str = None, show_reasoning: bool = True):
        """
        Initialize the Enhanced OSFI CAR agent with scoring.
        
        Args:
            pdf_directory: Path to directory containing OSFI CAR PDF files
            api_key: Google API key for Gemini (optional, reads from config if not provided)
            show_reasoning: Whether to display agent reasoning steps
        """
        self.pdf_directory = pdf_directory
        self.conversation_history = []
        self.reasoning_logger = ReasoningLogger(show_reasoning)
        self.scorer = ResponseScorer()
        
        # Set up API key
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            self._load_api_key_from_config()
        
        # Initialize components
        print("🔄 Initializing Enhanced OSFI CAR Agent with Reasoning & Scoring...")
        self._load_documents()
        self._create_vectorstore()
        self._setup_agent()
        print("✅ Enhanced OSFI CAR Agent with Mathematical Scoring ready!")
    
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
            "Configuring intelligent regulatory agent with scoring capabilities",
            thinking="Gemini 1.5 Pro provides strong reasoning capabilities for complex regulatory analysis with mathematical quality assessment"
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

Your responses will be mathematically scored for relevance and completeness, so ensure you:
- Address all parts of the question thoroughly
- Use retrieved regulatory content effectively
- Include specific references and examples
- Provide clear explanations and reasoning

Use your retrieval tool to gather comprehensive context before providing detailed regulatory guidance."""
        
        # Build workflow with enhanced state that includes retrieved chunks
        builder = StateGraph(EnhancedState)
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
            "Agent workflow configured with reasoning transparency and quality scoring",
            details={
                "llm_model": "Gemini 1.5 Pro",
                "workflow_nodes": ["llm_call", "tool_node"],
                "reasoning_enabled": True,
                "scoring_enabled": True
            },
            thinking="LangGraph workflow enables transparent decision-making, tool usage, and mathematical quality assessment"
        )
    
    def _enhanced_llm_call(self, state: MessagesState) -> Dict[str, Any]:
        """Enhanced LLM call with reasoning logging and response scoring."""
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
        
        # If this is a final response (no tool calls), score it
        if not has_tool_calls and user_message:
            response_content = result.content if hasattr(result, 'content') else str(result)
            retrieved_chunks = state.get("retrieved_chunks", [])
            
            # Debug: Check if chunks are available
            chunk_count = len(retrieved_chunks) if retrieved_chunks else 0
            chunk_words = sum(len(chunk.split()) for chunk in retrieved_chunks) if retrieved_chunks else 0
            
            # Score the response
            relevance_scores = self.scorer.score_relevance(user_message, response_content, retrieved_chunks)
            completeness_scores = self.scorer.score_completeness(user_message, response_content)
            
            # Calculate overall quality
            overall_quality = (relevance_scores['overall_relevance'] * 0.5 + 
                             completeness_scores['overall_completeness'] * 0.5)
            quality_grade = self.scorer.get_quality_grade(overall_quality)
            
            self.reasoning_logger.log_step(
                "scoring",
                f"Response Quality Assessment: {quality_grade} ({overall_quality:.3f}/1.0)",
                details={
                    "relevance_scores": relevance_scores,
                    "completeness_scores": completeness_scores,
                    "overall_quality": f"{overall_quality:.3f}",
                    "quality_grade": quality_grade,
                    "debug_chunk_info": f"{chunk_count} chunks, {chunk_words} words total"
                },
                thinking=f"Mathematical analysis shows response quality at {overall_quality:.3f}/1.0. "
                        f"Relevance: {relevance_scores['overall_relevance']:.3f}, "
                        f"Completeness: {completeness_scores['overall_completeness']:.3f}. "
                        f"Context: {chunk_count} chunks available for scoring."
            )
        
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
        """Enhanced tool execution with reasoning logging and retrieval scoring."""
        tool_calls = state["messages"][-1].tool_calls
        
        self.reasoning_logger.log_step(
            "tool_call",
            f"Executing {len(tool_calls)} retrieval operation(s)",
            thinking="Searching regulatory documents for relevant information to provide accurate guidance"
        )
        
        result = []
        all_retrieved_chunks = []
        
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
            
            # Store retrieved chunks for final scoring
            all_retrieved_chunks.append(observation)
            
            # Score the retrieved content quality
            retrieval_scores = self._score_retrieval_quality(query, observation)
            
            # Analyze retrieved content
            content_length = len(observation)
            word_count = len(observation.split())
            
            self.reasoning_logger.log_step(
                "evaluation",
                f"Retrieved {word_count} words with relevance score: {retrieval_scores['relevance']:.3f}/1.0",
                details={
                    "content_length": content_length,
                    "word_count": word_count,
                    "retrieval_time": f"{end_time - start_time:.2f}s",
                    "retrieval_scores": retrieval_scores,
                    "quality_assessment": retrieval_scores['quality_level']
                },
                thinking=f"Retrieved content quality: {retrieval_scores['quality_level']}. "
                        f"Strong relevance indicates good semantic matching for regulatory query."
            )
            
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        
        # Store retrieved chunks for final response scoring
        # In LangGraph, we need to return the state modifications
        return {"messages": result, "retrieved_chunks": all_retrieved_chunks}
    
    def _score_retrieval_quality(self, query: str, retrieved_content: str) -> Dict[str, Any]:
        """Score the quality of retrieved content."""
        # Simple relevance scoring
        keyword_overlap = self.scorer._keyword_overlap(query, retrieved_content)
        domain_relevance = self.scorer._domain_relevance(retrieved_content)
        
        # Average the scores
        relevance = (keyword_overlap + domain_relevance) / 2
        
        # Determine quality level
        if relevance >= 0.8:
            quality_level = "Excellent"
        elif relevance >= 0.6:
            quality_level = "Good"
        elif relevance >= 0.4:
            quality_level = "Fair"
        else:
            quality_level = "Poor"
        
        return {
            "relevance": relevance,
            "keyword_overlap": keyword_overlap,
            "domain_relevance": domain_relevance,
            "quality_level": quality_level
        }
    
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
        Ask the agent a question with full reasoning visibility and scoring.
        
        Args:
            question: User question about OSFI CAR regulations
            
        Returns:
            Agent response
        """
        # Reset step counter for new question
        self.reasoning_logger.step_count = 0
        
        self.reasoning_logger.log_step(
            "analysis",
            "Processing new regulatory query with quality scoring",
            details={"question": question},
            thinking="Starting comprehensive analysis to provide accurate regulatory guidance with mathematical quality assessment"
        )
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Get agent response
        self.reasoning_logger.log_step(
            "analysis",
            "Initiating agent workflow with scoring",
            thinking="Passing query through reasoning workflow to determine optimal response strategy and assess quality"
        )
        
        result = self.agent.invoke({"messages": self.conversation_history})
        
        # Extract response and update history
        response = result['messages'][-1].content
        self.conversation_history = result['messages']
        
        self.reasoning_logger.log_step(
            "synthesis",
            "Final response synthesized with quality assessment complete",
            details={
                "response_length": len(response),
                "total_reasoning_steps": self.reasoning_logger.step_count
            },
            thinking="Combined retrieved regulatory information with analysis to provide comprehensive guidance, mathematically assessed for quality"
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
    print("🧠  With Visible Agent Reasoning & Mathematical Quality Scoring")
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
    print("🎯 NEW: Mathematical Quality Scoring")
    print("• Relevance scores (0-1.0)")
    print("• Completeness scores (0-1.0)")  
    print("• Overall quality grades (A+ to C)")
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
    print("This enhanced agent shows its reasoning process and mathematically scores response quality.")
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
    print("📊 Evaluation")
    print("🎯 Quality scoring")
    print("✅ Conclusion")
    print("\n🎯 Quality Scoring:")
    print("• Relevance: How well response matches the question")
    print("• Completeness: How thorough and comprehensive")
    print("• Grades: A+ (Excellent) to C (Needs Improvement)")
    print()

def main():
    """Main interactive loop."""
    parser = argparse.ArgumentParser(description="Enhanced OSFI CAR Interactive Agent with Reasoning & Scoring")
    parser.add_argument("--pdf-dir", default="osfi car", 
                       help="Directory containing OSFI CAR PDF files")
    parser.add_argument("--api-key", help="Google API key for Gemini")
    parser.add_argument("--no-reasoning", action="store_true", 
                       help="Disable reasoning display")
    args = parser.parse_args()
    
    # Initialize agent
    try:
        agent = EnhancedOSFICARAgentWithScoring(
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
            
            # Get response with reasoning and scoring
            print(f"\n{'='*50}")
            print("🧠 AGENT REASONING PROCESS WITH QUALITY SCORING")
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