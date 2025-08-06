# OSFI CAR RAG Agent

A sophisticated Retrieval-Augmented Generation (RAG) agent for OSFI (Office of the Superintendent of Financial Institutions) Capital Adequacy Ratio regulatory compliance and analysis.

## 🎯 Overview

This project implements an intelligent regulatory assistant that provides expert guidance on OSFI CAR requirements and Basel III reforms. The agent features complete reasoning transparency, showing every step of its decision-making process.

## �� Key Features

### Core Capabilities
- **Intelligent Document Retrieval**: Semantic search across OSFI CAR regulatory documents
- **Expert Regulatory Guidance**: Comprehensive answers with specific regulatory references
- **Complete Reasoning Transparency**: Visible agent thinking and decision-making process
- **Batch Analysis**: Process multiple questions with detailed Markdown reports
- **Performance Monitoring**: Detailed metrics and analytics

### Agent Types
- **Interactive Agent** (`osfi_car_enhanced_reasoning.py`): Real-time chat with visible reasoning
- **Batch Analyzer** (`osfi_batch_analysis.py`): Process question lists with comprehensive reports
- **Standard Agent** (`osfi_car_chat.py`): Basic OSFI CAR assistance

## 📋 Requirements

- Python 3.8+
- Google Gemini API key
- OSFI CAR PDF documents

### Dependencies
```bash
pip install langchain langchain-community pypdf google-generativeai langgraph langchain-huggingface
```

## 🔧 Setup

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd pdf
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create a `config` file:
   ```
   api_key_gemini=YOUR_GOOGLE_API_KEY
   ```

3. **Add OSFI Documents**:
   Place OSFI CAR PDF files in the `osfi car/` directory

## 🎮 Usage

### Interactive Mode with Reasoning
```bash
source .venv/bin/activate
python osfi_car_enhanced_reasoning.py
```

### Batch Analysis
```bash
# Process questions from file
python osfi_batch_analysis.py -q questions.txt -o report.md

# Custom title and output
python osfi_batch_analysis.py -q questions.json -o analysis.md -t "OSFI Compliance Review"
```

### Standard Chat
```bash
python osfi_car_chat.py
```

## 📊 Architecture

### RAG Workflow
```
User Query → LLM Analysis → Decision Point → [Document Retrieval] → Response Generation
```

### Key Components
- **LangGraph State Machine**: Manages agent workflow and decision routing
- **Vector Store**: Semantic search across 634 document chunks (2000 tokens each)
- **Gemini 1.5 Pro**: Advanced reasoning and regulatory analysis
- **Reasoning Logger**: Complete transparency into agent thinking

### Retrieval Configuration
- **Chunk Size**: 2,000 tokens with 100-token overlap
- **References per Query**: 6 document chunks
- **Typical Retrieval**: 2,000-3,000 words of regulatory content
- **Performance**: 1-2 second retrieval times

## 📈 Sample Performance

- **Questions Processed**: 9 regulatory queries
- **Total Reasoning Steps**: 130 steps with complete transparency
- **Average Retrieval**: 2,330 words per query
- **Success Rate**: 100% accurate regulatory guidance

## 📝 Example Questions

- "What is the definition of default and the associated capital treatment of defaulted exposure?"
- "What is the minimum Common Equity Tier 1 capital ratio requirement?"
- "How do you calculate risk-weighted assets for credit risk?"
- "Explain the capital conservation buffer and when it applies"

## 📁 Project Structure

```
pdf/
├── osfi_car_enhanced_reasoning.py  # Main RAG agent with reasoning
├── osfi_batch_analysis.py          # Batch processing tool
├── osfi_car_chat.py               # Standard chat agent
├── test_enhanced_reasoning.py      # Testing framework
├── README_batch_analysis.md        # Detailed batch tool guide
├── sample_questions.txt            # Example questions
├── sample_questions.json           # JSON format examples
├── osfi car/                       # OSFI PDF documents directory
└── reports/                        # Generated analysis reports
```

## 🧠 Reasoning Transparency

The agent shows complete decision-making process:

```
🧠 Agent Thinking Process [Step 3] (21:26:00)
   Action: Evaluating user query and determining response strategy
   Reasoning: Need to analyze question complexity and decide whether 
            regulatory document retrieval is necessary

🔍 Agent Thinking Process [Step 8] (21:26:13)
   Action: Searching OSFI documents for: 'definition of default AND defaulted exposures'
   Reasoning: Semantic search will find most relevant regulatory sections
```

## 📊 Generated Reports

Batch analysis creates comprehensive Markdown reports with:
- Executive summary with statistics
- Step-by-step reasoning for each question
- Complete regulatory guidance with OSFI references
- Performance analytics and patterns

## 🔬 Testing

```bash
# Test enhanced reasoning
python test_enhanced_reasoning.py

# Interactive demo
python test_enhanced_reasoning.py --interactive

# Batch analysis test
python osfi_batch_analysis.py -q test_questions.txt -o test_report.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is for educational and compliance purposes. Ensure proper licensing for commercial use.

## ⚠️ Disclaimer

This tool provides regulatory guidance based on OSFI documents but should not replace professional regulatory advice. Always consult with qualified professionals for implementation decisions.

---

**Built with LangChain, LangGraph, and Google Gemini AI**
