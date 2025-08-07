# LangChain JSON Search Tool

## 🎯 Overview

This LangChain tool wraps the JSON searcher functionality into a standardized LangChain `BaseTool` that can be used with LangChain agents, workflows, and applications. It provides intelligent search and data fetching capabilities for processed document data (PDFs, Excel, CSV) stored in JSON format.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install langchain langchain-community pydantic

# Or install from requirements
pip install -r requirements_langchain_tool.txt
```

### Basic Usage

```python
from langchain_json_searcher_tool import create_json_search_tool

# Create the tool
tool = create_json_search_tool("../Fetch_data/unified_results.json")

# Use directly
result = tool._run(operation="discover")
print(result)
```

### LangChain Agent Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain_json_searcher_tool import create_json_search_tool

# Create tool and agent
json_tool = create_json_search_tool()
llm = OpenAI(temperature=0)

agent = initialize_agent(
    tools=[json_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Ask natural language questions
response = agent.run("What files are available in the dataset?")
response = agent.run("Find all mentions of 'capital requirements'")
response = agent.run("Get page 5 from the PDF document")
```

## 📚 Available Operations

### 1. File Discovery
List all available files in the dataset.

```python
tool._run(operation="discover")
```

### 2. Full File Content
Get complete content from a specific file.

```python
tool._run(
    operation="get_full_file",
    filename="document.pdf"
)
```

### 3. Single Item Retrieval
Get specific page/sheet from a file.

```python
# Get PDF page
tool._run(
    operation="get_single_item",
    filename="document.pdf", 
    page=5
)

# Get Excel sheet
tool._run(
    operation="get_single_item",
    filename="spreadsheet.xlsx",
    sheet="Balance Sheet"
)
```

### 4. Metadata Search
Search in file metadata (NOT content).

```python
tool._run(
    operation="search_metadata",
    search_value="document.pdf",
    field="source_file",
    search_type="exact"
)
```

### 5. Content Search
Search in actual document text.

```python
tool._run(
    operation="search_content",
    search_value="capital requirements",
    search_type="partial"
)
```

## 🛠️ Parameters Reference

### Required Parameters by Operation

| Operation | Required Parameters | Optional Parameters |
|-----------|-------------------|-------------------|
| `discover` | None | `json_file_path` |
| `get_full_file` | `filename` | `json_file_path` |
| `get_single_item` | `filename` + (`page` OR `sheet`) | `json_file_path`, `chunk` |
| `search_metadata` | `search_value` | `json_file_path`, `field`, `search_type` |
| `search_content` | `search_value` | `json_file_path`, `search_type` |

### Parameter Details

- **operation**: The search operation to perform
- **json_file_path**: Path to JSON file (default: "../Fetch_data/unified_results.json")
- **filename**: Target filename for file operations
- **search_value**: Text or value to search for
- **field**: Metadata field to search ("source_file", "page_number", etc.)
- **search_type**: "exact", "partial", or "regex"
- **page**: Page number for PDF content
- **sheet**: Sheet name for Excel content  
- **chunk**: Chunk index for PDF content

## 🔍 Response Format

### Success Response
```json
{
  "summary": {
    "operation": "Content Search Results",
    "status": "SUCCESS", 
    "input_parameters": {...},
    "summary": "Found 15 matches for 'capital requirements'"
  },
  "detailed_results": {
    "status": "success",
    "search_value": "capital requirements",
    "total_results": 15,
    "results": [...]
  }
}
```

### Error Response
```json
{
  "status": "ERROR",
  "error_type": "MissingParameter",
  "message": "filename is required for get_full_file operation",
  "details": "Example: {'operation': 'get_full_file', 'filename': 'document.pdf'}",
  "suggestion": "Provide a valid filename",
  "available_operations": [...],
  "example_usage": {...}
}
```

## 🚨 Error Handling

The tool provides comprehensive error handling with detailed feedback:

### Common Error Types

1. **FileNotFound**: JSON file doesn't exist
2. **InvalidJSON**: JSON parsing errors  
3. **MissingParameter**: Required parameter not provided
4. **InvalidOperation**: Unknown operation specified
5. **OperationError**: Error during operation execution

### Error Response Features

- Clear error type classification
- Detailed error messages
- Specific suggestions for fixes
- Example usage patterns
- List of available operations

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_langchain_tool.py
```

The test script covers:
- All 5 core operations
- Error handling scenarios
- Parameter validation
- Integration examples

### Test Modes

```bash
# Full test suite
python test_langchain_tool.py

# Simple demo only
python test_langchain_tool.py simple

# Integration examples only
python test_langchain_tool.py integration
```

## 📊 Use Cases

### 1. Document Q&A Systems
```python
# Agent answers: "What regulatory documents do we have?"
agent.run("List all the files in our document database")
```

### 2. Compliance Searches
```python
# Agent finds regulatory requirements
agent.run("Find all mentions of capital requirements in our documents")
```

### 3. Financial Data Extraction
```python
# Agent extracts financial statements
agent.run("Get the Balance Sheet data from our financial spreadsheet")
```

### 4. Document Navigation
```python
# Agent retrieves specific sections
agent.run("Show me page 10 of the regulatory document")
```

## 🔧 Advanced Usage

### Custom JSON File Path
```python
# Use with different JSON file
tool = create_json_search_tool("path/to/my_data.json")
```

### Regex Searches
```python
# Find complex patterns
tool._run(
    operation="search_content",
    search_value="balance.*sheet|income.*statement", 
    search_type="regex"
)
```

### Metadata Filtering
```python
# Find documents by processing date
tool._run(
    operation="search_metadata",
    search_value="2025-08-06",
    field="processing_timestamp",
    search_type="partial"  
)
```

## 🎯 Integration Tips

### With LangChain Agents
- Use descriptive agent prompts that leverage the tool's capabilities
- The tool works well with ZERO_SHOT_REACT_DESCRIPTION agents
- Consider using with memory for multi-turn conversations

### With Custom Applications
- The tool returns structured JSON for easy parsing
- Error responses include examples for user guidance
- Status codes allow programmatic error handling

### Performance Considerations
- Metadata searches are faster than content searches
- Use specific filenames when possible to reduce search scope
- Cache frequently accessed results

## 🔗 Dependencies

- **langchain**: Core LangChain framework
- **langchain-community**: Community tools and integrations
- **pydantic**: Data validation and settings management
- **json, re, pathlib**: Built-in Python modules

## 📝 Contributing

To extend the tool:

1. Add new operations to the `_execute_operation` method
2. Update the `JSONSearchInput` schema with new parameters
3. Add corresponding test cases
4. Update documentation

## 🐛 Troubleshooting

### Tool Not Found
```python
# Ensure proper import path
from langchain_json_searcher_tool import create_json_search_tool
```

### JSON File Issues
```python
# Check file exists and is valid JSON
import json
with open("../Fetch_data/unified_results.json", 'r') as f:
    data = json.load(f)  # Should not raise error
```

### Agent Integration Issues
```python
# Verify tool is properly added to agent
print(f"Agent tools: {[tool.name for tool in agent.tools]}")
```

## 📄 License

This tool is part of the JSON Search and Data Fetching project. See main project documentation for license details.

---

## 📚 Related Documentation

- [JSON Searcher README](README.md) - Core functionality documentation
- [Examples](examples.py) - Usage examples
- [Technical Requirements](../TECHNICAL_REQUIREMENTS.md) - Project technical details