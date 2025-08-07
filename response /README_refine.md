# Refine Synthesis Tool
**Advanced Content Processing with Batch Refine Chain**

A specialized tool for processing large retrieved content using the refine chain approach with Gemini API. Handles token overflow by processing chunks in batches and iteratively refining responses.

## 🚀 Key Features

### Core Capabilities
- **Refine Chain Processing**: Iteratively improve responses with each content batch
- **Smart Batch Management**: Automatic token limit handling and optimal batch sizing
- **Gemini API Integration**: Uses Google's Gemini 1.5 Pro for high-quality synthesis
- **JSON Format Support**: Direct processing of your retrieval system outputs
- **Simple Interface**: Easy-to-use functions for quick integration

### Token Management
- **No Content Loss**: Process unlimited chunks without truncation
- **Smart Batching**: Automatic batch size calculation based on token limits
- **Chunk Prioritization**: Relevance-based ordering for optimal refine sequence

## 📦 Installation & Setup

### Prerequisites
```bash
# Install dependencies
pip install -r requirements_refine.txt

# Set API key
export GEMINI_API_KEY='your_gemini_api_key_here'
```

### Dependencies
```
google-generativeai>=0.8.0
python-dotenv>=1.0.0
tiktoken>=0.5.0
```

## 🛠️ Usage

### 1. Simple Function Interface

#### Process Content Chunks
```python
from refine_synthesis_tool import simple_refine_synthesis

# Your content chunks
chunks = [
    "OSFI Capital Adequacy Requirements specify minimum capital ratios...",
    "Risk-weighted assets must be calculated using standardized approaches...", 
    "The capital conservation buffer is set at 2.5% of risk-weighted assets..."
]

# Generate response
response = simple_refine_synthesis(
    user_query="What are OSFI capital requirements?",
    chunks=chunks,
    api_key="your_key"  # Optional if set in environment
)

print(response)
```

#### Process JSON Files Directly
```python
from refine_synthesis_tool import process_json_file_simple

# Process your retrieval JSON files
response = process_json_file_simple(
    json_file_path="inputs/output_testing/test_01_1_file_discovery.json",
    user_query="What files are available?",  # Optional - will be inferred
    api_key="your_key"  # Optional if set in environment
)

print(response)
```

### 2. Advanced Interface

#### Full Control with Metadata
```python
from refine_synthesis_tool import RefineSynthesisTool

# Initialize tool
tool = RefineSynthesisTool()

# Process with full metadata
result = tool.refine_synthesis(
    user_query="Analyze the financial data",
    chunks=your_chunks,
    prioritize=True  # Reorder chunks by relevance
)

# Access detailed results
print("Response:", result['response'])
print("Batches used:", result['metadata']['total_batches'])
print("Processing time:", result['metadata']['total_processing_time'])
print("Strategy:", result['metadata']['processing_strategy'])
```

#### Process Your JSON Files
```python
# Process JSON from your retrieval system
result = tool.process_json_file(
    "inputs/output_testing/test_13_13_natural_language_test___specific_page.json",
    user_query="Explain the regulatory requirements"
)

# Full result structure
{
    'response': 'Generated comprehensive response...',
    'metadata': {
        'total_chunks': 3,
        'total_batches': 1,
        'processing_strategy': 'single_batch',
        'total_processing_time': 4.23
    },
    'processing_log': [
        {
            'batch_number': 1,
            'chunk_count': 3,
            'action': 'initial_synthesis'
        }
    ],
    'config': {
        'model_name': 'gemini-1.5-pro',
        'chunks_per_batch_limit': 1887,
        'max_content_tokens': 995000
    }
}
```

### 3. Command Line Interface

#### Test the Tool
```bash
python refine_synthesis_tool.py --test
```

#### Process JSON File
```bash
python refine_synthesis_tool.py \
    --json-file "inputs/output_testing/test_14_14_natural_language_test___excel_data.json" \
    --query "Analyze the balance sheet data" \
    --output "results.json"
```

#### Custom API Key
```bash
python refine_synthesis_tool.py \
    --json-file "your_file.json" \
    --api-key "your_gemini_key" \
    --query "Your question"
```

## 📊 How Refine Chain Works

### Single Batch Processing (Small Content)
```
User Query + Chunks (1-5) → Gemini API → Final Response
```

### Multi-Batch Processing (Large Content)  
```
Batch 1: Initial Synthesis
User Query + Chunks 1-368 → Gemini → Initial Response

Batch 2: First Refine
Current Response + Chunks 369-736 → Gemini → Refined Response  

Batch 3: Second Refine
Current Response + Chunks 737-1104 → Gemini → Final Response
```

### Chunk Prioritization
```python
# Chunks ordered by relevance to user query
chunks = prioritize_chunks(all_chunks, user_query)

# Most relevant chunks processed first = stronger foundation
# Less relevant chunks refine and add details
```

## 🎯 Your Data Format Support

### Supported JSON Formats

#### PDF Content
```json
{
  "response": {
    "detailed_results": {
      "type": "pdf_chunk",
      "content": "Regulatory text content...",
      "page": 5,
      "words": 486
    }
  }
}
```

#### Excel Data
```json
{
  "response": {
    "detailed_results": {
      "type": "excel_table", 
      "content": {
        "columns": ["Category", "Item", "Amount"],
        "data": [{"Category": "Assets", "Item": "Cash", "Amount": 1000000}]
      }
    }
  }
}
```

#### Search Results
```json
{
  "response": {
    "detailed_results": {
      "results": [
        {
          "filename": "car24_chpt1_0.pdf",
          "page": 1,
          "match_preview": "OSFI capital requirements..."
        }
      ]
    }
  }
}
```

#### File Discovery
```json
{
  "response": {
    "detailed_results": {
      "files": ["TechTrend_Financials_2024.xlsx", "car24_chpt1_0.pdf"]
    }
  }
}
```

## 📈 Performance & Scaling

### Token Limits & Batching
Based on your actual data analysis:

- **Average chunk size**: ~530 tokens (396 words)
- **Gemini 1.5 Pro limit**: 1M tokens context
- **Chunks per batch**: ~1,887 chunks
- **Your PDF (26 chunks)**: Single batch processing ✅
- **OSFI search (40 results)**: Single batch processing ✅
- **Large datasets (200+ chunks)**: Multi-batch refine chain 🔄

### Processing Examples

| Content Size | Strategy | Batches | Est. Time |
|--------------|----------|---------|-----------|
| 26 PDF chunks | Single batch | 1 | 3-5 seconds |
| 40 search results | Single batch | 1 | 4-6 seconds |
| 200 chunks | Multi-batch | 1 | 8-12 seconds |
| 1000 chunks | Multi-batch | 1 | 15-25 seconds |

## 🧪 Testing & Examples

### Run Test Examples
```bash
python test_refine_examples.py
```

This shows:
- ✅ File discovery processing
- ✅ Multi-chunk PDF content refine
- ✅ Simple function interfaces
- ✅ Expected JSON outputs

### Test with Your Actual Data
```bash
# Test with your file discovery JSON
python refine_synthesis_tool.py \
    --json-file "inputs/output_testing/test_01_1_file_discovery.json" \
    --test

# Test with PDF content
python refine_synthesis_tool.py \
    --json-file "inputs/output_testing/test_13_13_natural_language_test___specific_page.json" \
    --query "Explain the regulatory requirements in detail"
```

## 🔧 Configuration Options

### RefineConfig Parameters
```python
config = RefineConfig(
    model_name="gemini-1.5-pro",           # Gemini model
    max_tokens_per_request=1000000,        # Context limit
    response_reserve_tokens=4000,          # Reserve for response
    prompt_overhead_tokens=1000,           # Reserve for prompts
    average_chunk_tokens=530,              # Based on your data
    temperature=0.1                        # Deterministic responses
)

tool = RefineSynthesisTool(config=config)
```

### Environment Variables
```bash
export GEMINI_API_KEY='your_key_here'
export GEMINI_MODEL='gemini-1.5-pro'  # Optional
```

## 🚀 Integration Examples

### With Your Existing Pipeline
```python
# Step 1: Your retrieval system generates JSON
retrieval_result = your_retrieval_system.search("OSFI requirements")

# Step 2: Refine tool processes the results  
from refine_synthesis_tool import process_json_file_simple

response = process_json_file_simple(
    retrieval_result.json_file,
    user_query="What are the OSFI capital requirements?"
)

# Step 3: Return comprehensive response
return response
```

### Batch Processing Multiple Files
```python
import glob
from refine_synthesis_tool import RefineSynthesisTool

tool = RefineSynthesisTool()

# Process all your test files
for json_file in glob.glob("inputs/output_testing/*.json"):
    if "session_summary" not in json_file:  # Skip summary files
        print(f"Processing: {json_file}")
        result = tool.process_json_file(json_file)
        
        # Save results
        output_file = f"processed_{Path(json_file).stem}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
```

## 🔍 Troubleshooting

### Common Issues

#### API Key Not Found
```
Error: Gemini API key required
Solution: export GEMINI_API_KEY='your_key_here'
```

#### Rate Limiting
```
Error: Quota exceeded
Solution: Add retry logic or reduce batch sizes
```

#### Large Content Processing
```
Issue: Very large datasets (1000+ chunks)
Solution: Increase batch processing or use hierarchical summarization
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
tool = RefineSynthesisTool()
result = tool.refine_synthesis(query, chunks)
```

## 📝 License & Support

Part of the document analysis pipeline project. The refine synthesis tool provides robust content processing for your retrieval system with guaranteed comprehensive responses regardless of content size.

**Version**: 1.0  
**Last Updated**: 2025-08-06  
**Author**: AI Development Team

---

**Ready to use with your existing retrieval JSON files! 🎉**