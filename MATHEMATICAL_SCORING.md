# Mathematical Scoring System
## OSFI CAR RAG Agent Quality Assessment

### 📊 Overview
The enhanced OSFI CAR RAG agent uses a **6-metric mathematical scoring system** to quantitatively assess response quality on a 0.0-1.0 scale with letter grades (A+ to C).

---

## 🔢 Core Formula

```
Overall Quality = (Relevance × 0.5) + (Completeness × 0.5)
```

### Relevance Score (50% weight)
```
Relevance = (Keyword_Overlap × 0.4) + (Citation_Relevance × 0.2) + (Domain_Relevance × 0.4)
```

### Completeness Score (50% weight)
```
Completeness = (Info_Density × 0.3) + (Question_Coverage × 0.25) + (Reference_Quality × 0.25) + (Explanation_Depth × 0.2)
```

---

## 📈 Individual Metrics

### **1. Keyword Overlap** (Relevance)
```python
score = matching_words / total_question_words
```
- **Purpose**: Direct question-response alignment
- **Range**: 0.0 - 1.0

### **2. Citation Relevance** (Relevance) 🆕
```python
citation_count = detect_regulatory_patterns(response)
citation_density = citation_count / (word_count / 100)
score = min(1.0, citation_density × 0.3)
```
- **Purpose**: Detects regulatory document usage via citations
- **Innovation**: Replaces problematic context usage metric
- **Patterns**: Chapter/section refs, table citations, Basel III terms

### **3. Domain Relevance** (Relevance)
```python
found_keywords = count_regulatory_terms(response)
score = min(1.0, found_keywords / total_regulatory_keywords)
```
- **Purpose**: Regulatory terminology density
- **Keywords**: 15+ OSFI/Basel specific terms

### **4. Information Density** (Completeness)
```python
structured_elements = count_lists_paragraphs_formatting(response)
score = min(1.0, (structured_elements + detail_indicators) / response_length × 100)
```
- **Purpose**: Rich, structured content assessment

### **5. Question Coverage** (Completeness)
```python
addressed_parts = analyze_multi_part_question(question, response)
score = addressed_parts / total_question_parts
```
- **Purpose**: Comprehensive question component coverage

### **6. Reference Quality** (Completeness)
```python
specific_citations = count_specific_regulatory_refs(response)
general_citations = count_general_regulatory_refs(response)
score = min(1.0, specific_citations + general_citations)  # Capped at 1.0
```
- **Purpose**: Specific regulatory citation quality
- **Fix**: Proper 1.0 maximum capping

### **7. Explanation Depth** (Completeness)
```python
explanatory_patterns = count_explanatory_phrases(response)
word_factor = word_count / 100
score = min(1.0, (explanatory_patterns × 0.5) + word_factor)
```
- **Purpose**: Explanatory reasoning quality
- **Patterns**: 40+ causal, clarifying, definition phrases

---

## 🎯 Quality Grading Scale

| Score Range | Letter Grade | Description |
|-------------|--------------|-------------|
| 0.90 - 1.00 | **A+** | Excellent |
| 0.80 - 0.89 | **A** | Very Good |
| 0.70 - 0.79 | **B+** | Good |
| 0.60 - 0.69 | **B** | Satisfactory |
| 0.50 - 0.59 | **C+** | Needs Improvement |
| 0.40 - 0.49 | **C** | Poor |
| 0.00 - 0.39 | **F** | Fail |

---

## 📊 Production Performance

### Test Results (9 regulatory questions)
- **Average Overall Quality**: 0.805/1.0 (**A grade**)
- **Average Relevance**: 0.823/1.0
- **Average Completeness**: 0.786/1.0

### Grade Distribution
- **A (Very Good)**: 66.7% (6/9 questions)
- **B+ (Good)**: 22.2% (2/9 questions)  
- **B (Satisfactory)**: 11.1% (1/9 questions)

---

## 🔧 Technical Implementation

### Citation Detection Patterns
```python
citation_patterns = [
    r'\b(chapter|section|paragraph)\s+[\d\.]+',  # Chapter 1, Section 2.3
    r'\btable\s+\d+',                            # Table 1, Table 2
    r'\b(basel|osfi)\s+(iii|car|guideline)',     # Basel III, OSFI CAR
    r'\b(cat(egory)?\s+[iv]+|d-sibs?)',         # Category I, D-SIBs
    r'\brisk[- ]weighted\s+assets?',            # Risk-weighted assets
    r'\bcapital\s+(adequacy|conservation)'       # Capital adequacy
]
```

### Explanatory Phrase Patterns (40+ patterns)
```python
explanatory_patterns = [
    r'\b(because|due to|as a result|therefore|consequently)',
    r'\b(for example|such as|including|specifically)',
    r'\b(defined as|means|refers to|indicates)',
    r'\b(step by step|process|procedure|method)',
    # ... 35+ more patterns
]
```

---

## ✅ Key Innovations

1. **Citation-Based Relevance**: Solves LangGraph state management issues
2. **Proper Score Capping**: All metrics bounded to 0.0-1.0 range
3. **Enhanced Pattern Recognition**: 40+ explanatory phrases vs original 8
4. **Production Validation**: 100% success rate on regulatory test suite
5. **Mathematical Transparency**: Complete formula visibility and auditability

---

## 🎯 Usage in Reports

The scoring system generates:
- **Executive Summaries**: Average scores and grade distributions
- **Per-Question Assessment**: Detailed 6-metric breakdown
- **Quality Transparency**: Complete mathematical calculations shown
- **Production Metrics**: Real-time quality assessment during processing

---

*This mathematical framework ensures consistent, quantifiable quality assessment for regulatory AI responses with full transparency and auditability.*