# AI Report Generator Suite
**Complete Document Analysis & Report Generation System**

---

## 🚀 Overview

This suite provides a complete solution for processing document retrieval results and generating comprehensive AI-powered reports using the Refine Synthesis Tool with Gemini API.

### Key Components

1. **`generic_report_generator.py`** - Main script for generating reports
2. **`refine_synthesis_tool.py`** - Advanced processing engine  
3. **`inputs/`** - Sample JSON files from retrieval system
4. **`archive/`** - Backup of development files and examples

---

## 📋 Quick Start

### 1. Prerequisites
- Python 3.8+ with virtual environment activated
- Gemini API key in `.env` file (parent directory)
- Required dependencies installed

### 2. Setup
```bash
# Ensure virtual environment is active
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements_refine.txt

# Verify .env file contains API key
cat ../.env | grep gemini_api_key
```

### 3. Generate Your First Report
```bash
# Run with default configuration (Market Risk Analysis)
python generic_report_generator.py
```

---

## 🛠️ Customization

### Edit Configuration
Open `generic_report_generator.py` and modify the `CONFIG` section:

```python
CONFIG = {
    # Input Configuration
    "json_file_path": "inputs/output_testing/your_file.json",
    
    # Query Configuration  
    "user_query": "Your custom analysis question",
    
    # Output Configuration
    "output_filename": "Your_Report_Name",
    "report_title": "Your Report Title",
    "report_subtitle": "Your Subtitle",
    
    # Processing Options
    "prioritize_chunks": True,
    "include_metadata": True,
    "include_processing_log": True,
}
```

### Available Input Files

| File | Type | Description |
|------|------|-------------|
| `test_01_1_file_discovery.json` | Discovery | Available files list |
| `test_02_2_search_content___valid.json` | Search | OSFI search results (40 matches) |
| `test_03_3_get_full_file___pdf.json` | Full Document | Complete CAR PDF (52 chunks) |
| `test_04_4_get_single_item___specific_page.json` | Page Content | Specific regulatory page |
| `test_13_13_natural_language_test___specific_page.json` | Page Content | Natural language version |
| `test_14_14_natural_language_test___excel_data.json` | Excel Data | Financial balance sheet |

### Example Configurations

#### Financial Analysis
```python
CONFIG = {
    "json_file_path": "inputs/output_testing/test_14_14_natural_language_test___excel_data.json",
    "user_query": "Analyze the financial data and provide insights on company performance",
    "output_filename": "Financial_Analysis_Report",
    "report_title": "Financial Performance Analysis",
}
```

#### Regulatory Research
```python
CONFIG = {
    "json_file_path": "inputs/output_testing/test_02_2_search_content___valid.json", 
    "user_query": "Analyze OSFI regulatory requirements and provide key insights",
    "output_filename": "OSFI_Analysis_Report",
    "report_title": "OSFI Regulatory Requirements Analysis",
}
```

#### Document Discovery
```python
CONFIG = {
    "json_file_path": "inputs/output_testing/test_01_1_file_discovery.json",
    "user_query": "Provide a comprehensive summary of available files and their contents",
    "output_filename": "File_Discovery_Report", 
    "report_title": "Document Repository Analysis",
}
```

---

## 📊 Processing Features

### Refine Synthesis Engine
- **Smart Batching**: Automatic token management
- **Chunk Prioritization**: Relevance-based ordering
- **No Content Loss**: Process unlimited document size
- **Quality Assessment**: Mathematical scoring system

### Output Features
- **Professional Reports**: Well-structured Markdown output
- **Processing Metadata**: Complete transparency into AI decisions
- **Quality Metrics**: Relevance and completeness scoring
- **Timestamped Results**: Trackable report generation

---

## 📁 Directory Structure

```
response/
├── generic_report_generator.py    # 🎯 MAIN SCRIPT
├── refine_synthesis_tool.py       # Processing engine
├── requirements_refine.txt        # Dependencies
├── README.md                      # This file
├── README_refine.md              # Detailed technical docs
├── inputs/                       # Sample JSON files
│   └── output_testing/
│       ├── test_01_1_file_discovery.json
│       ├── test_02_2_search_content___valid.json
│       ├── test_03_3_get_full_file___pdf.json
│       └── ... (more test files)
└── archive/                      # Development backups
    ├── demo_reports/             # Example outputs
    ├── old_scripts/              # Development versions
    └── temp_files/               # Temporary files
```

---

## 🎯 Usage Examples

### Generate Market Risk Report
```bash
python generic_report_generator.py
# Uses default config for OSFI Market Risk analysis
```

### Quick File Analysis
```bash
# Edit CONFIG section for different file
# Change json_file_path to desired input
python generic_report_generator.py
```

### Batch Different Reports
```bash
# 1. Edit CONFIG for Financial Analysis
python generic_report_generator.py

# 2. Edit CONFIG for Regulatory Analysis  
python generic_report_generator.py

# 3. Edit CONFIG for Document Discovery
python generic_report_generator.py
```

---

## 📈 Performance

### Processing Capabilities
- **Small Files** (1-5 chunks): ~3-5 seconds
- **Medium Files** (10-20 chunks): ~8-15 seconds  
- **Large Files** (50+ chunks): ~25-35 seconds
- **Massive Content**: Automatic batch processing

### Quality Assessment
- **Average Quality**: 0.80+ / 1.0 (A grade)
- **Relevance Scoring**: Keyword + citation + domain analysis
- **Completeness Scoring**: Information density + coverage analysis

---

## 🔧 Troubleshooting

### Common Issues

#### API Key Not Found
```
Error: gemini_api_key not found in environment
Solution: Check ../.env file contains gemini_api_key=YOUR_KEY
```

#### File Not Found
```
Error: Input file not found
Solution: Verify json_file_path in CONFIG section
```

#### Dependencies Missing
```
Error: No module named 'google'
Solution: pip install -r requirements_refine.txt
```

### Debug Mode
```python
# Add to script for verbose output
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📚 Additional Resources

- **`README_refine.md`** - Detailed technical documentation
- **`archive/demo_reports/`** - Example generated reports
- **`archive/old_scripts/`** - Development history
- **Input JSON files** - Sample retrieval results for testing

---

## 🎉 Success Metrics

### Tested Performance
- ✅ **52 chunk processing** (27,366 tokens) in 30 seconds
- ✅ **Professional report generation** with AI analysis
- ✅ **Quality scoring** with A-grade results
- ✅ **Complete transparency** in processing steps
- ✅ **Flexible configuration** for different use cases

**Ready to generate professional AI-powered reports from your document retrieval results!** 🚀

---

**Version**: 1.0  
**Last Updated**: 2025-08-06  
**Author**: AI Development Team