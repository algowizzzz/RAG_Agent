# Agent Content Package

## 🎯 Overview

The `agent_content` package contains integrated LangChain tools for intelligent document discovery, search, and AI synthesis. This package implements the correct flow for data-informed analysis:

```
User Query + JSONSearchTool (discovery and metadata) → JSONSearchTool (operations) → RefineSynthesisTool → Comprehensive Response
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GEMINI_API_KEY="your_api_key_here"
```

### Basic Usage

```python
from agent_content import create_integrated_discovery_synthesis_tool

# Create the integrated tool
tool = create_integrated_discovery_synthesis_tool("../Fetch_data/unified_results.json")

# Use with natural language queries
result = tool._run(user_query="Get me the summary of CAR car pdf")
```

### LangChain Agent Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from agent_content import create_integrated_discovery_synthesis_tool

# Create tool and agent
tool = create_integrated_discovery_synthesis_tool()
llm = OpenAI(temperature=0)

agent = initialize_agent(
    tools=[tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Ask complex questions
response = agent.run("What are the capital requirements for market risk?")
```

## 📚 Components

### 1. IntegratedDiscoverySynthesisTool
The main tool that orchestrates the complete flow:
- **Discovery Phase**: Uses JSONSearchTool to understand available data
- **Analysis Phase**: Combines user query with discovery results to determine operations
- **Execution Phase**: Runs targeted JSONSearchTool operations
- **Synthesis Phase**: Uses RefineSynthesisTool for comprehensive responses

### 2. JSONSearchTool
Core search operations on processed documents:
- `discover` - List all available files
- `search_content` - Search document text
- `get_full_file` - Get complete file content
- `get_single_item` - Get specific page/sheet
- `search_metadata` - Search file metadata

### 3. RefineSynthesisTool
AI-powered synthesis using Gemini API:
- Handles large content through batch processing
- Prioritizes chunks by relevance
- Provides comprehensive responses with reasoning

## 🧪 Testing

```bash
# Run comprehensive tests
python test_integrated_tool.py

# The test demonstrates:
# 1. Discovery of available files
# 2. Query analysis and operation determination
# 3. Content retrieval and processing
# 4. AI synthesis and response generation
```

## 📊 Example Use Cases

### Document Summarization
```python
result = tool._run(user_query="Provide a summary of the CAR document")
```

### Regulatory Analysis
```python
result = tool._run(user_query="What are the capital requirements for market risk according to OSFI?")
```

### Financial Data Extraction
```python
result = tool._run(user_query="Show me the Balance Sheet data from the financial spreadsheet")
```

### Multi-Document Analysis
```python
result = tool._run(user_query="What regulatory frameworks are discussed across all documents?")
```

## 🔧 Configuration

### Custom JSON File Path
```python
tool = create_integrated_discovery_synthesis_tool("/path/to/your/unified_results.json")
```

### Custom Synthesis Configuration
```python
result = tool._run(
    user_query="Your question",
    max_results=30,
    include_reasoning=True,
    synthesis_config={
        "temperature": 0.1,
        "max_tokens_per_request": 1000000
    }
)
```

## 🎯 Flow Verification

The tool implements and verifies the correct flow:

1. **User Query + Discovery/Metadata** → Understand available data landscape
2. **Operation Determination** → Combine query intent with actual data to determine optimal operations
3. **JSONSearchTool Operations** → Execute targeted search and retrieval operations
4. **RefineSynthesisTool Processing** → Generate comprehensive AI responses
5. **Comprehensive Response** → Return results with full reasoning transparency

## 📄 Files Structure

```
agent_content/
├── __init__.py                              # Package initialization
├── README.md                                # This file
├── requirements.txt                         # Dependencies
├── integrated_discovery_synthesis_tool.py   # Main integrated tool
├── langchain_json_searcher_tool.py         # JSON search operations
├── json_searcher.py                        # Core search functions
├── refine_synthesis_tool.py                # AI synthesis tool
├── test_integrated_tool.py                 # Comprehensive tests
├── requirements_langchain_tool.txt         # LangChain specific deps
└── requirements_refine.txt                 # Synthesis specific deps
```

## 🚨 Prerequisites

- Python 3.8+
- Gemini API key (set as `GEMINI_API_KEY` environment variable)
- Processed document data in `unified_results.json` format
- LangChain framework for agent integration

## 🎉 Success Metrics

Based on testing with CAR PDF:
- ✅ **Discovery**: Successfully identifies available files
- ✅ **Operation Selection**: Data-informed operation determination
- ✅ **Content Retrieval**: Efficient extraction of relevant content
- ✅ **Synthesis Quality**: Comprehensive, well-structured responses
- ✅ **Processing Speed**: ~44 seconds for 52 chunks (27K tokens)
- ✅ **Reasoning Transparency**: Full visibility into LLM decisions

---

**Next Steps**: Use this package in your LangChain workflows for intelligent document analysis and question answering.