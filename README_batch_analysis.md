# OSFI CAR Batch Analysis Tool

## Overview

The OSFI CAR Batch Analysis Tool processes multiple regulatory questions and generates comprehensive Markdown reports with complete agent reasoning, decision-making steps, and regulatory guidance.

## Features

✅ **Batch Processing** - Process multiple questions automatically  
✅ **Complete Reasoning Visibility** - Shows every step of agent thinking  
✅ **Professional Markdown Output** - Publication-ready reports  
✅ **Multiple Input Formats** - Support for .txt and .json question files  
✅ **Detailed Analytics** - Reasoning pattern analysis and statistics  
✅ **Error Handling** - Graceful handling of failed analyses  

## Quick Start

### 1. Prepare Your Questions

**Text Format (questions.txt):**
```
What is the definition of default and the associated capital treatment of defaulted exposure?
What is the minimum Common Equity Tier 1 capital ratio requirement?
How do you calculate risk-weighted assets for credit risk?
```

**JSON Format (questions.json):**
```json
{
  "questions": [
    "What is the definition of default and the associated capital treatment of defaulted exposure?",
    "What is the minimum Common Equity Tier 1 capital ratio requirement?",
    "How do you calculate risk-weighted assets for credit risk?"
  ]
}
```

### 2. Run the Analysis

```bash
# Basic usage
source .venv/bin/activate
python osfi_batch_analysis.py -q questions.txt -o report.md

# With custom title
python osfi_batch_analysis.py -q questions.txt -o report.md -t "My OSFI Analysis"

# Using JSON input
python osfi_batch_analysis.py -q questions.json -o comprehensive_report.md
```

### 3. Review Your Report

The generated Markdown file contains:
- Executive summary with statistics
- Complete reasoning process for each question
- Regulatory guidance with OSFI references
- Pattern analysis and insights

## Command Line Options

```
--questions, -q     Path to questions file (.txt or .json) [REQUIRED]
--output, -o        Output Markdown file (default: osfi_car_analysis_report.md)
--title, -t         Report title (default: "OSFI CAR Analysis Report")
--pdf-dir          PDF directory (default: "osfi car")
--api-key          Google API key for Gemini
```

## Sample Questions

### Basic Regulatory Questions
- What is the minimum Common Equity Tier 1 capital ratio requirement?
- How do you calculate risk-weighted assets for credit risk?
- What are the components of Tier 1 capital?

### Complex Analysis Questions
- What is the definition of default and the associated capital treatment of defaulted exposure?
- Explain the difference between the standardized approach and internal ratings-based approach
- How are operational risk capital requirements calculated under Basel III?

### Implementation Questions
- What are the eligibility criteria for regulatory capital instruments?
- Explain the treatment of mortgage exposures under the standardized approach
- How does the capital conservation buffer work in practice?

## Report Structure

### Executive Summary
- Total questions processed
- Success/failure statistics
- Total reasoning steps

### Individual Question Analysis
For each question:
1. **🧠 Agent Reasoning Process** - Step-by-step thinking
2. **📊 Reasoning Summary** - Statistics and patterns
3. **🤖 Regulatory Guidance** - Complete OSFI guidance with references

### Appendix
- Reasoning pattern analysis
- Document retrieval statistics
- Overall insights

## Advanced Usage

### Custom Question Files

**Structured JSON with Metadata:**
```json
{
  "title": "OSFI CAR Compliance Review",
  "description": "Questions for annual compliance assessment",
  "questions": [
    "What is the minimum CET1 ratio?",
    "How do we calculate operational risk capital?"
  ],
  "metadata": {
    "department": "Risk Management",
    "review_date": "2024-08-05"
  }
}
```

### Batch Processing Large Question Sets

For large question sets (50+ questions):
1. Split into smaller batches for better performance
2. Use descriptive output filenames
3. Monitor processing time and memory usage

```bash
# Process in batches
python osfi_batch_analysis.py -q batch_1_questions.txt -o batch_1_report.md
python osfi_batch_analysis.py -q batch_2_questions.txt -o batch_2_report.md
```

## Sample Output Structure

```markdown
# OSFI CAR Analysis Report

## Executive Summary
- Total Questions Processed: 10
- Successful Analyses: 10
- Total Reasoning Steps: 140

## Analysis Results

### Question 1
**Query:** *What is the minimum CET1 ratio?*

#### 🧠 Agent Reasoning Process
**🤔 Step 1 - Decision**
- Action: Evaluating user query complexity
- Reasoning: Need to determine if document retrieval is required

**🔍 Step 2 - Retrieval**  
- Action: Searching OSFI documents for: "minimum CET1 ratio"
- Reasoning: Semantic search will find relevant regulatory sections

#### 🤖 Regulatory Guidance
[Complete regulatory guidance with OSFI references]
```

## Performance Tips

1. **Virtual Environment**: Always use the Python virtual environment
2. **API Key**: Ensure Google API key is configured in config file
3. **Question Quality**: Well-formed questions get better reasoning visibility
4. **Batch Size**: Process 10-20 questions at a time for optimal performance

## Troubleshooting

### Common Issues

**Import Error:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate
```

**API Key Error:**
```bash
# Check config file has api_key_gemini=YOUR_KEY
cat config
```

**Memory Issues:**
- Reduce batch size
- Clear conversation history between runs
- Monitor system resources

### Error Recovery

If analysis fails for some questions:
- Check the generated report for error details
- Re-run with individual questions to isolate issues
- Verify PDF documents are accessible

## Integration

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run OSFI Analysis
  run: |
    source .venv/bin/activate
    python osfi_batch_analysis.py -q compliance_questions.txt -o reports/monthly_analysis.md
```

### Automated Reporting
```bash
#!/bin/bash
# Monthly compliance check
DATE=$(date +%Y-%m)
python osfi_batch_analysis.py \
  -q monthly_questions.txt \
  -o "reports/osfi_analysis_${DATE}.md" \
  -t "OSFI CAR Monthly Analysis - ${DATE}"
```

## Files Generated by This Tool

- `osfi_batch_analysis.py` - Main batch analysis script
- `sample_questions.txt` - Text format example
- `sample_questions.json` - JSON format example  
- `test_questions.txt` - Small test set
- `test_report.md` - Sample generated report

## Next Steps

1. Create your question file
2. Run the batch analysis
3. Review the generated Markdown report
4. Use insights for compliance and training
5. Integrate into your regulatory workflow

---

*For support or feature requests, refer to the main OSFI CAR agent documentation.*