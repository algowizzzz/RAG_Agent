# Technical Requirements Document (TRD)
## OSFI CAR RAG Agent with Mathematical Scoring v2.0

**Document Version:** 1.0  
**Date:** 2025-08-05  
**Author:** AI Development Team  
**Project:** OSFI CAR Enhanced Reasoning Agent

---

## 1. Executive Summary

This TRD defines the technical requirements for the OSFI CAR RAG Agent v2.0, an advanced regulatory compliance assistant featuring mathematical quality assessment, citation-based relevance scoring, and comprehensive batch analysis capabilities.

### 1.1 Project Scope
- Enhanced RAG agent for OSFI Capital Adequacy Ratio regulatory guidance
- Mathematical scoring system for response quality assessment
- Batch processing with comprehensive quality reports
- Production-ready system with 100% test suite success rate

---

## 2. System Architecture

### 2.1 Core Components

#### 2.1.1 Enhanced RAG Agent (`osfi_car_enhanced_reasoning_with_scoring.py`)
- **Primary Class**: `EnhancedOSFICARAgent`
- **State Management**: LangGraph `EnhancedState` with chunk persistence
- **LLM Integration**: Google Gemini 1.5 Pro with temperature=0.1
- **Vector Store**: InMemoryVectorStore with HuggingFace embeddings

#### 2.1.2 Mathematical Scoring System (`ResponseScorer`)
- **Relevance Metrics**: 3 components (keyword overlap, citation relevance, domain relevance)
- **Completeness Metrics**: 4 components (info density, question coverage, reference quality, explanation depth)
- **Quality Grading**: A+ to C scale with numerical scores 0.0-1.0

#### 2.1.3 Batch Analysis Engine (`osfi_batch_analysis_with_scoring.py`)
- **Input Processing**: Text files and JSON question formats
- **Report Generation**: Comprehensive Markdown with executive summaries
- **Quality Analytics**: Grade distribution and performance metrics

### 2.2 Data Flow Architecture

```
Input Query → LangGraph State Machine → [Document Retrieval] → Response Generation → Mathematical Scoring → Quality Report
```

---

## 3. Functional Requirements

### 3.1 Core Functionality

#### 3.1.1 Document Processing
- **Requirement**: Process OSFI CAR PDF documents into searchable chunks
- **Specification**: 2000-token chunks with 100-token overlap
- **Performance**: Sub-2 second retrieval times
- **Quality**: 634 document chunks with semantic embeddings

#### 3.1.2 Query Processing
- **Requirement**: Handle complex regulatory queries with reasoning transparency
- **Specification**: Multi-step reasoning with visible decision process
- **Output**: Complete reasoning logs with 15+ steps per query
- **Quality**: Real-time quality assessment with mathematical scoring

#### 3.1.3 Mathematical Scoring
- **Requirement**: Quantitative quality assessment of responses
- **Specification**: 6-metric system with 0.0-1.0 scoring range
- **Components**:
  - **Relevance**: `(keyword_overlap × 0.4) + (citation_relevance × 0.2) + (domain_relevance × 0.4)`
  - **Completeness**: `(info_density × 0.3) + (question_coverage × 0.25) + (reference_quality × 0.25) + (explanation_depth × 0.2)`
  - **Overall**: `(relevance × 0.5) + (completeness × 0.5)`

### 3.2 Quality Requirements

#### 3.2.1 Accuracy
- **Target**: 100% successful processing of regulatory queries
- **Measurement**: No system failures or invalid responses
- **Current**: 9/9 test questions processed successfully

#### 3.2.2 Quality Assessment
- **Target**: Average quality score ≥ 0.8/1.0
- **Current**: 0.805/1.0 achieved on standard test suite
- **Distribution**: 66.7% A grade, 22.2% B+ grade, 11.1% B grade

#### 3.2.3 Performance
- **Response Time**: ≤ 60 seconds per complex regulatory query
- **Current**: ~53 seconds average processing time
- **Retrieval**: 1-2 seconds for document search

---

## 4. Technical Specifications

### 4.1 Software Requirements

#### 4.1.1 Core Dependencies
```python
langchain>=0.1.0
langchain-community>=0.0.20
langchain-google-genai>=0.0.6
langgraph>=0.0.30
langchain-huggingface>=0.0.1
pypdf>=4.0.0
python-dotenv>=1.0.0
```

#### 4.1.2 Python Environment
- **Version**: Python 3.8+
- **Virtual Environment**: Required (.venv)
- **Package Management**: pip with requirements.txt

#### 4.1.3 API Requirements
- **Google Gemini API**: Valid API key in .env file
- **Environment Variable**: `gemini_api_key=YOUR_API_KEY`
- **Model**: Gemini 1.5 Pro with 128k context window

### 4.2 Data Requirements

#### 4.2.1 Input Documents
- **Format**: PDF documents (OSFI CAR regulatory materials)
- **Location**: `osfi car/` directory
- **Processing**: Automatic chunking and embedding generation

#### 4.2.2 Test Data
- **Test Suite**: `test_questions.txt` (9 regulatory questions)
- **Format**: Plain text, one question per line
- **Coverage**: Capital adequacy, risk-weighted assets, default definitions, etc.

### 4.3 Output Specifications

#### 4.3.1 Interactive Mode
- **Format**: Real-time console output with reasoning steps
- **Quality Display**: Live scoring with A+ to C grades
- **Transparency**: Complete decision-making process visibility

#### 4.3.2 Batch Reports
- **Format**: Comprehensive Markdown documents
- **Structure**: Executive summary + detailed analysis + methodology
- **Size**: ~75KB for 9-question analysis
- **Content**: Quality scores, reasoning logs, regulatory guidance

---

## 5. Mathematical Scoring Specifications

### 5.1 Relevance Scoring Components

#### 5.1.1 Keyword Overlap
- **Formula**: `overlap_words / total_question_words`
- **Range**: 0.0 - 1.0
- **Purpose**: Measures direct question-response alignment

#### 5.1.2 Citation Relevance
- **Method**: Regex pattern detection for regulatory citations
- **Patterns**: Chapter/section references, table citations, regulatory terms
- **Formula**: `min(1.0, citation_density × 0.3)`
- **Innovation**: Replaces problematic context usage metric

#### 5.1.3 Domain Relevance
- **Method**: Regulatory keyword density analysis
- **Keywords**: 15+ OSFI/Basel III specific terms
- **Formula**: `min(1.0, found_keywords / total_keywords)`

### 5.2 Completeness Scoring Components

#### 5.2.1 Information Density
- **Method**: Structured content detection (lists, paragraphs, formatting)
- **Formula**: `min(1.0, (structured_elements + detail_indicators) / response_length × 100)`

#### 5.2.2 Question Coverage
- **Method**: Multi-part question component analysis
- **Formula**: `addressed_parts / total_parts`

#### 5.2.3 Reference Quality
- **Method**: Specific regulatory citation detection
- **Cap**: 1.0 maximum (fixed from original >1.0 issue)
- **Formula**: `min(1.0, specific_score + general_score)`

#### 5.2.4 Explanation Depth
- **Method**: Explanatory phrase pattern matching
- **Patterns**: 40+ causal, clarifying, and definition phrases
- **Formula**: `min(1.0, (pattern_count × 0.5) + (words / 100))`

---

## 6. Implementation Details

### 6.1 State Management

#### 6.1.1 LangGraph Enhanced State
```python
class EnhancedState(MessagesState):
    retrieved_chunks: List[str]  # Critical for scoring persistence
```

#### 6.1.2 State Flow
1. **Tool Node**: Stores retrieved chunks in state
2. **LLM Node**: Accesses chunks for quality scoring
3. **Persistence**: Chunks maintained across graph transitions

### 6.2 Quality Assessment Integration

#### 6.2.1 Retrieval Quality Scoring
- **Location**: `_enhanced_tool_node` method
- **Timing**: During document retrieval
- **Output**: Retrieval quality metrics logged

#### 6.2.2 Final Response Scoring
- **Location**: `_enhanced_llm_call` method
- **Timing**: After response generation
- **Output**: Complete 6-metric quality assessment

### 6.3 Report Generation

#### 6.3.1 Batch Processing Flow
1. **Question Loading**: Text/JSON file parsing
2. **Agent Processing**: Enhanced agent with scoring
3. **Report Compilation**: Markdown generation with quality analytics
4. **Executive Summary**: Automated statistics and grade distribution

---

## 7. Testing and Validation

### 7.1 Test Suite

#### 7.1.1 Standard Test Questions
- **File**: `test_questions.txt`
- **Count**: 9 regulatory questions
- **Coverage**: OSFI CAR comprehensive regulatory topics
- **Expected**: 100% processing success, ≥0.8 average quality

#### 7.1.2 Quality Benchmarks
- **Relevance**: ≥0.8 average across all metrics
- **Completeness**: ≥0.75 average across all metrics
- **Citation Detection**: Variable based on regulatory content density
- **Grade Distribution**: Majority A/B+ grades

### 7.2 Performance Testing

#### 7.2.1 Processing Speed
- **Individual Query**: ≤60 seconds
- **Batch Analysis**: Linear scaling with question count
- **Memory Usage**: Efficient vector store management

#### 7.2.2 Quality Consistency
- **Reproducibility**: Consistent scoring across runs
- **Calibration**: Meaningful grade distinctions
- **Accuracy**: Scores reflect actual response quality

---

## 8. Security and Compliance

### 8.1 API Security
- **Key Management**: Environment variables only
- **No Hardcoding**: API keys excluded from source code
- **.env Files**: Gitignored for security

### 8.2 Data Handling
- **Document Privacy**: Local processing only
- **No Data Persistence**: Temporary embeddings in memory
- **Regulatory Compliance**: OSFI document handling protocols

---

## 9. Deployment Requirements

### 9.1 Environment Setup
1. **Python Virtual Environment**: Isolated dependency management
2. **API Key Configuration**: .env file with Gemini credentials
3. **Document Preparation**: OSFI PDFs in designated directory
4. **Dependency Installation**: Full requirements.txt installation

### 9.2 Production Readiness
- **Error Handling**: Graceful failure management
- **Logging**: Comprehensive reasoning and scoring logs
- **Documentation**: Complete user and technical documentation
- **Testing**: 100% success rate on standard test suite

---

## 10. Future Enhancements

### 10.1 Potential Improvements
- **Multi-Model Support**: Integration with additional LLMs
- **Advanced Scoring**: Machine learning-based quality metrics
- **Database Integration**: Persistent conversation history
- **API Development**: REST API for external integration

### 10.2 Scalability Considerations
- **Document Volume**: Support for larger regulatory document sets
- **Concurrent Processing**: Multi-user batch analysis
- **Performance Optimization**: Caching and optimization strategies

---

**Document End**

*This TRD serves as the authoritative technical specification for the OSFI CAR RAG Agent v2.0 with Mathematical Scoring system.*