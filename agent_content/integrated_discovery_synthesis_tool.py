#!/usr/bin/env python3
"""
LangChain Integrated Discovery and Synthesis Tool
================================================

This tool combines user queries with discovery and metadata search results to determine
optimal JSONSearchTool operations, then uses RefineSynthesisTool for comprehensive responses.

Correct Flow:
User Query + JSONSearchTool (discovery and metadata results) → JSONSearchTool (operation/s) → RefineSynthesisTool → Comprehensive Response

Features:
- Uses discovery results to understand available data landscape
- Combines user query with metadata to determine optimal operations
- Executes targeted JSONSearchTool operations based on combined analysis
- Processes results through RefineSynthesisTool for synthesis
- Full visibility into LLM decision-making process

Author: AI Development Team
Date: 2025-08-06
Version: 1.0
"""

import json
import os
from datetime import datetime
from typing import Optional, Type, Dict, Any, Union, List
from pathlib import Path

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Import existing tools and functionality from agent_content directory
from langchain_json_searcher_tool import JSONSearchTool, create_json_search_tool
from refine_synthesis_tool import RefineSynthesisTool, RefineConfig


class IntegratedDiscoverySynthesisInput(BaseModel):
    """Input schema for the Integrated Discovery and Synthesis Tool."""
    
    user_query: str = Field(
        ...,
        description="The user's question or request that will be combined with discovery results to determine operations"
    )
    
    json_file_path: str = Field(
        default="../Fetch_data/unified_results.json",
        description="Path to the JSON file containing the processed documents"
    )
    
    max_results: int = Field(
        default=50,
        description="Maximum number of search results to retrieve for synthesis"
    )
    
    gemini_api_key: Optional[str] = Field(
        None,
        description="Gemini API key for synthesis (optional if set in environment)"
    )
    
    include_reasoning: bool = Field(
        default=True,
        description="Whether to include detailed reasoning about LLM decisions in the response"
    )
    
    synthesis_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom configuration for the refine synthesis process"
    )


class IntegratedDiscoverySynthesisTool(BaseTool):
    """
    LangChain tool that follows the correct flow:
    User Query + JSONSearchTool (discovery and metadata results) → JSONSearchTool (operation/s) → RefineSynthesisTool → Comprehensive Response
    
    This tool:
    1. Executes discovery and metadata search using JSONSearchTool
    2. Combines user query with discovery/metadata results to determine optimal operations
    3. Executes the determined JSONSearchTool operations
    4. Feeds results to RefineSynthesisTool for comprehensive synthesis
    5. Provides full visibility into the decision-making process
    """
    
    name: str = "integrated_discovery_synthesis"
    description: str = """
    Tool that combines user queries with discovery and metadata results to determine optimal search operations and synthesis.
    
    Correct Flow:
    1. User Query + Discovery Results + Metadata Results → Determine Operations
    2. Execute JSONSearchTool Operations
    3. Synthesize Results with RefineSynthesisTool
    
    This tool automatically:
    - Runs discovery to understand available files and data types
    - Performs metadata searches to understand data structure
    - Combines query intent with available data to determine optimal operations
    - Executes targeted JSONSearchTool operations
    - Uses RefineSynthesisTool for comprehensive response generation
    - Provides detailed reasoning about all decisions made
    
    Perfect for:
    - Complex document Q&A requiring data-informed operation selection
    - Queries that need to understand available data before searching
    - Analysis requiring optimal search strategy based on actual data landscape
    
    Input: Provide a user_query - discovery and metadata analysis happens automatically.
    Output: Comprehensive analysis with supporting evidence and full decision reasoning.
    
    Example:
    {"user_query": "What are the key capital requirements for market risk according to OSFI regulations?"}
    """
    args_schema: Type[BaseModel] = IntegratedDiscoverySynthesisInput

    def __init__(self):
        super().__init__()
        # Initialize tools as class attributes (not Pydantic model fields)
        object.__setattr__(self, 'json_search_tool', None)
        object.__setattr__(self, 'synthesis_tool', None)
        
    def _initialize_tools(self, json_file_path: str, api_key: str = None, synthesis_config: Dict = None):
        """Initialize the search and synthesis tools."""
        if not self.json_search_tool:
            object.__setattr__(self, 'json_search_tool', create_json_search_tool(json_file_path))
        
        if not self.synthesis_tool:
            config = RefineConfig()
            if synthesis_config:
                for key, value in synthesis_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            object.__setattr__(self, 'synthesis_tool', RefineSynthesisTool(api_key=api_key, config=config))

    def _run(self, **kwargs) -> str:
        """Execute the correct flow: User Query + Discovery/Metadata → Operations → Synthesis."""
        
        start_time = datetime.now()
        processing_log = []
        
        try:
            # Parse and validate input
            inputs = IntegratedDiscoverySynthesisInput(**kwargs)
            
            # Initialize tools
            self._initialize_tools(
                inputs.json_file_path, 
                inputs.gemini_api_key, 
                inputs.synthesis_config
            )
            
            # Step 1: Discovery and Metadata Collection
            discovery_results, metadata_results = self._discovery_and_metadata_phase(inputs, processing_log)
            
            # Step 2: Intelligent Size-Based Processing Decision
            processing_strategy = self._determine_processing_strategy(
                inputs, discovery_results, processing_log
            )
            
            if processing_strategy["approach"] == "direct_synthesis":
                # Small dataset: Send entire JSON directly to synthesis
                synthesis_result = self._direct_synthesis_phase(
                    inputs, discovery_results, processing_strategy, processing_log
                )
                operations_plan = {"strategy": "direct_synthesis", "operations": []}
                retrieved_content = {"summary": {"approach": "direct_synthesis"}}
                
            else:
                # Large dataset: Use discovery → targeted retrieval → refine synthesis
                # Step 3: Combine User Query with Discovery/Metadata to Determine Operations
                operations_plan = self._determine_operations_from_query_and_data(
                    inputs, discovery_results, metadata_results, processing_log
                )
                
                # Step 4: Execute Determined JSONSearchTool Operations
                retrieved_content = self._execute_determined_operations(
                    inputs, operations_plan, processing_log
                )
                
                # Step 5: RefineSynthesisTool Processing
                synthesis_result = self._synthesis_phase(inputs, retrieved_content, processing_log)
            
            # Step 5: Compile comprehensive response
            total_time = (datetime.now() - start_time).total_seconds()
            
            return self._format_comprehensive_response(
                inputs, synthesis_result, processing_log, total_time,
                discovery_results, metadata_results, operations_plan
            )
            
        except Exception as e:
            return self._format_error_response(str(e), kwargs.get('user_query', 'Unknown'))

    def _discovery_and_metadata_phase(self, inputs: IntegratedDiscoverySynthesisInput, 
                                    processing_log: List) -> tuple:
        """Phase 1: Run discovery and metadata searches using JSONSearchTool."""
        
        phase_start = datetime.now()
        
        # Execute discovery
        discovery_raw = self.json_search_tool._run(operation="discover")
        discovery_result = json.loads(discovery_raw)
        
        # Execute metadata search to understand data structure
        # Search for common metadata patterns
        metadata_searches = [
            {"operation": "search_metadata", "search_value": "pdf", "field": "source_file", "search_type": "partial"},
            {"operation": "search_metadata", "search_value": "xlsx", "field": "source_file", "search_type": "partial"},
            {"operation": "search_metadata", "search_value": "csv", "field": "source_file", "search_type": "partial"}
        ]
        
        metadata_results = []
        for search_params in metadata_searches:
            try:
                metadata_raw = self.json_search_tool._run(**search_params)
                metadata_result = json.loads(metadata_raw)
                if metadata_result.get('summary', {}).get('status') == 'SUCCESS':
                    metadata_results.append({
                        "search_params": search_params,
                        "result": metadata_result
                    })
            except Exception as e:
                metadata_results.append({
                    "search_params": search_params,
                    "error": str(e)
                })
        
        # Log the discovery and metadata collection
        reasoning = {
            "discovery_reasoning": "Executed discovery to understand available files and data landscape",
            "metadata_reasoning": "Searched metadata by file type to understand data structure and availability",
            "files_discovered": discovery_result.get('summary', {}).get('files', []),
            "metadata_patterns_found": len([r for r in metadata_results if 'result' in r]),
            "data_landscape_summary": self._analyze_data_landscape(discovery_result, metadata_results)
        }
        
        processing_log.append({
            "phase": "discovery_and_metadata",
            "duration_seconds": (datetime.now() - phase_start).total_seconds(),
            "status": "completed",
            "reasoning": reasoning,
            "discovery_result": discovery_result,
            "metadata_results": metadata_results
        })
        
        return discovery_result, metadata_results

    def _analyze_data_landscape(self, discovery_result: Dict, metadata_results: List) -> Dict:
        """Analyze the data landscape from discovery and metadata results."""
        
        files = discovery_result.get('detailed_results', {}).get('files', [])
        file_details = discovery_result.get('detailed_results', {}).get('details', [])
        
        landscape = {
            "total_files": len(files),
            "file_types": {},
            "content_volume": {"total_words": 0, "total_chunks": 0},
            "data_sources": []
        }
        
        for detail in file_details:
            file_type = detail.get('file_type', 'unknown')
            landscape["file_types"][file_type] = landscape["file_types"].get(file_type, 0) + 1
            landscape["content_volume"]["total_words"] += detail.get('words', 0)
            if detail.get('chunks') != 'N/A':
                landscape["content_volume"]["total_chunks"] += detail.get('chunks', 0)
            
            landscape["data_sources"].append({
                "filename": detail.get('filename'),
                "type": file_type,
                "size_indicator": "large" if detail.get('words', 0) > 5000 else "medium" if detail.get('words', 0) > 1000 else "small"
            })
        
        return landscape

    def _determine_processing_strategy(self, inputs: IntegratedDiscoverySynthesisInput,
                                     discovery_results: Dict, processing_log: List) -> Dict:
        """Phase 2: Determine processing strategy based on content size (100k word threshold)."""
        
        phase_start = datetime.now()
        
        # Calculate total word count from discovery results
        total_words = 0
        content_breakdown = []
        
        detailed_results = discovery_results.get('detailed_results', {})
        if 'details' in detailed_results:
            for file_detail in detailed_results['details']:
                words = file_detail.get('words', 0)
                total_words += words
                content_breakdown.append({
                    "filename": file_detail.get('filename'),
                    "words": words,
                    "type": file_detail.get('file_type')
                })
        
        # Define threshold (100k words)
        WORD_THRESHOLD = 100000
        
        # Determine strategy
        if total_words < WORD_THRESHOLD:
            approach = "direct_synthesis"
            reasoning = f"Dataset is small ({total_words:,} words < {WORD_THRESHOLD:,} threshold). Using direct synthesis for efficiency."
        else:
            approach = "retrieval_synthesis"
            reasoning = f"Dataset is large ({total_words:,} words ≥ {WORD_THRESHOLD:,} threshold). Using targeted retrieval + refine synthesis to prevent token overflow."
        
        strategy = {
            "approach": approach,
            "total_words": total_words,
            "word_threshold": WORD_THRESHOLD,
            "reasoning": reasoning,
            "content_breakdown": content_breakdown,
            "efficiency_gain": "direct_synthesis" if approach == "direct_synthesis" else "targeted_processing"
        }
        
        processing_log.append({
            "phase": "processing_strategy_determination",
            "duration_seconds": (datetime.now() - phase_start).total_seconds(),
            "status": "completed",
            "strategy": strategy
        })
        
        print(f"🧠 Processing Strategy: {approach}")
        print(f"📊 Total words: {total_words:,} ({'< threshold' if total_words < WORD_THRESHOLD else '≥ threshold'})")
        print(f"💡 Reasoning: {reasoning}")
        
        return strategy

    def _direct_synthesis_phase(self, inputs: IntegratedDiscoverySynthesisInput,
                              discovery_results: Dict, processing_strategy: Dict,
                              processing_log: List) -> Dict:
        """Direct synthesis phase: Load entire JSON and synthesize directly (for small datasets)."""
        
        phase_start = datetime.now()
        
        # Load the entire JSON file
        try:
            with open(inputs.json_file_path, 'r', encoding='utf-8') as f:
                full_json_data = json.load(f)
            
            print(f"📄 Loading entire JSON file for direct synthesis...")
            
            # Extract all content chunks from the entire JSON
            all_chunks = []
            
            # Process all items in the JSON
            for item_key, item_data in full_json_data.items():
                if isinstance(item_data, dict):
                    if 'content' in item_data:
                        # Direct content
                        all_chunks.append(item_data['content'])
                    elif 'chunks' in item_data:
                        # Chunked content
                        for chunk in item_data['chunks']:
                            if isinstance(chunk, dict) and 'content' in chunk:
                                all_chunks.append(chunk['content'])
                            elif isinstance(chunk, str):
                                all_chunks.append(chunk)
                    elif 'data' in item_data:
                        # Structured data (like Excel)
                        formatted_content = self._format_structured_data(item_data)
                        if formatted_content:
                            all_chunks.append(formatted_content)
            
            print(f"📦 Extracted {len(all_chunks)} chunks from entire dataset")
            
            # Apply limit if needed
            if len(all_chunks) > inputs.max_results:
                print(f"⚠️  Limiting to {inputs.max_results} chunks due to max_results setting")
                all_chunks = all_chunks[:inputs.max_results]
            
            # Direct synthesis using RefineSynthesisTool
            if all_chunks:
                synthesis_result = self.synthesis_tool.refine_synthesis(
                    user_query=inputs.user_query,
                    chunks=all_chunks,
                    prioritize=True
                )
            else:
                synthesis_result = {
                    "response": f"No content found in the dataset to answer: '{inputs.user_query}'",
                    "metadata": {
                        "synthesis_performed": False,
                        "reason": "No content chunks found in JSON file"
                    }
                }
            
            processing_log.append({
                "phase": "direct_synthesis",
                "duration_seconds": (datetime.now() - phase_start).total_seconds(),
                "status": "completed",
                "total_chunks_processed": len(all_chunks),
                "synthesis_approach": "direct_full_dataset",
                "efficiency_benefit": "No retrieval overhead, direct processing"
            })
            
            return synthesis_result
            
        except Exception as e:
            processing_log.append({
                "phase": "direct_synthesis",
                "duration_seconds": (datetime.now() - phase_start).total_seconds(),
                "status": "error",
                "error": str(e)
            })
            
            return {
                "response": f"Error in direct synthesis: {str(e)}",
                "metadata": {
                    "synthesis_performed": False,
                    "reason": f"Direct synthesis failed: {str(e)}"
                }
            }

    def _format_structured_data(self, item_data: Dict) -> str:
        """Format structured data (like Excel) into readable text for synthesis."""
        if 'data' in item_data and 'columns' in item_data:
            # Excel-like data
            data = item_data['data']
            columns = item_data['columns']
            
            formatted = f"Structured Data - Columns: {', '.join(columns)}\n\n"
            for i, row in enumerate(data[:10]):  # Limit to first 10 rows for efficiency
                formatted += f"Row {i+1}:\n"
                for col in columns:
                    value = row.get(col, 'N/A')
                    formatted += f"  {col}: {value}\n"
                formatted += "\n"
            
            if len(data) > 10:
                formatted += f"... and {len(data) - 10} more rows\n"
                
            return formatted
        
        return None

    def _determine_operations_from_query_and_data(self, inputs: IntegratedDiscoverySynthesisInput,
                                                discovery_results: Dict, metadata_results: List,
                                                processing_log: List) -> Dict:
        """Phase 2: Combine user query with discovery/metadata results to determine optimal operations."""
        
        phase_start = datetime.now()
        
        query = inputs.user_query.lower()
        available_files = discovery_results.get('summary', {}).get('files', [])
        data_landscape = self._analyze_data_landscape(discovery_results, metadata_results)
        
        # Analysis combining query intent with actual available data
        analysis = {
            "query_analysis": {
                "original_query": inputs.user_query,
                "key_terms_extracted": [],
                "file_references_detected": [],
                "data_type_preferences": [],
                "scope_assessment": ""
            },
            "data_landscape_analysis": data_landscape,
            "operation_determination": {
                "reasoning": "",
                "selected_operations": [],
                "justification": ""
            }
        }
        
        # Extract key terms from query
        key_terms = []
        query_words = query.split()
        
        # Look for regulatory/financial terms
        regulatory_terms = ["osfi", "capital", "requirement", "risk", "basel", "regulatory"]
        financial_terms = ["balance sheet", "income", "financial", "assets", "liabilities"]
        specific_terms = ["market risk", "credit risk", "operational risk"]
        
        for term in regulatory_terms + financial_terms + specific_terms:
            if term in query:
                key_terms.append(term)
                if term in regulatory_terms:
                    analysis["query_analysis"]["data_type_preferences"].append("regulatory_documents")
                elif term in financial_terms:
                    analysis["query_analysis"]["data_type_preferences"].append("financial_data")
        
        analysis["query_analysis"]["key_terms_extracted"] = key_terms
        
        # Check for specific file references in query
        for filename in available_files:
            file_base = filename.lower().replace('.pdf', '').replace('.xlsx', '').replace('.csv', '')
            if any(part in query for part in file_base.split('_')):
                analysis["query_analysis"]["file_references_detected"].append(filename)
        
        # Assess query scope
        if len(key_terms) > 3 or "comprehensive" in query or "analyze" in query:
            analysis["query_analysis"]["scope_assessment"] = "comprehensive"
        elif len(key_terms) > 1:
            analysis["query_analysis"]["scope_assessment"] = "targeted"
        else:
            analysis["query_analysis"]["scope_assessment"] = "specific"
        
        # Determine operations based on combined analysis
        operations = []
        
        # If specific files mentioned, prioritize those
        if analysis["query_analysis"]["file_references_detected"]:
            for filename in analysis["query_analysis"]["file_references_detected"]:
                operations.append({
                    "operation": "get_full_file",
                    "filename": filename,
                    "justification": f"Query specifically references {filename}"
                })
        
        # Add content searches for key terms
        for term in key_terms[:3]:  # Limit to top 3 terms to avoid overload
            operations.append({
                "operation": "search_content",
                "search_value": term,
                "search_type": "partial",
                "justification": f"Key term '{term}' from query analysis"
            })
        
        # If no specific operations determined, use broad search
        if not operations:
            # Extract most meaningful words from query
            meaningful_words = [w for w in query_words if len(w) > 4 and w not in 
                             ['what', 'where', 'when', 'how', 'why', 'are', 'the', 'and', 'for']]
            if meaningful_words:
                operations.append({
                    "operation": "search_content",
                    "search_value": meaningful_words[0],
                    "search_type": "partial",
                    "justification": "Broad content search based on main query term"
                })
        
        analysis["operation_determination"]["selected_operations"] = operations
        analysis["operation_determination"]["reasoning"] = (
            f"Based on query scope assessment '{analysis['query_analysis']['scope_assessment']}' "
            f"and available data landscape with {data_landscape['total_files']} files, "
            f"determined {len(operations)} operations combining file-specific and content searches."
        )
        analysis["operation_determination"]["justification"] = (
            "Operations selected by combining user query intent with actual available data structure, "
            "prioritizing specific file references and key term content searches."
        )
        
        processing_log.append({
            "phase": "operation_determination",
            "duration_seconds": (datetime.now() - phase_start).total_seconds(),
            "status": "completed",
            "analysis": analysis,
            "operations_planned": len(operations)
        })
        
        return analysis

    def _execute_determined_operations(self, inputs: IntegratedDiscoverySynthesisInput,
                                     operations_plan: Dict, processing_log: List) -> Dict:
        """Phase 3: Execute the operations determined from query + data analysis."""
        
        phase_start = datetime.now()
        all_retrieved_content = []
        execution_results = []
        
        operations = operations_plan["operation_determination"]["selected_operations"]
        
        for i, operation_spec in enumerate(operations):
            op_start = datetime.now()
            
            # Extract operation parameters
            operation_params = {k: v for k, v in operation_spec.items() if k != "justification"}
            
            try:
                # Execute the JSONSearchTool operation
                search_result_raw = self.json_search_tool._run(**operation_params)
                search_result = json.loads(search_result_raw)
                
                # Extract content chunks using RefineSynthesisTool's extraction method
                chunks = self.synthesis_tool.extract_chunks_from_json({
                    "response": search_result
                })
                
                execution_result = {
                    "operation_index": i,
                    "operation_params": operation_params,
                    "justification": operation_spec.get("justification", ""),
                    "duration_seconds": (datetime.now() - op_start).total_seconds(),
                    "chunks_retrieved": len(chunks),
                    "status": "success",
                    "result_summary": search_result.get('summary', {})
                }
                
                all_retrieved_content.extend(chunks)
                execution_results.append(execution_result)
                
            except Exception as e:
                execution_result = {
                    "operation_index": i,
                    "operation_params": operation_params,
                    "justification": operation_spec.get("justification", ""),
                    "duration_seconds": (datetime.now() - op_start).total_seconds(),
                    "chunks_retrieved": 0,
                    "status": "error",
                    "error": str(e)
                }
                execution_results.append(execution_result)
        
        # Remove duplicates and apply limits
        unique_chunks = list(dict.fromkeys(all_retrieved_content))
        if len(unique_chunks) > inputs.max_results:
            unique_chunks = unique_chunks[:inputs.max_results]
        
        retrieval_summary = {
            "total_operations_executed": len(operations),
            "successful_operations": len([r for r in execution_results if r["status"] == "success"]),
            "total_chunks_retrieved": len(all_retrieved_content),
            "unique_chunks_after_deduplication": len(unique_chunks),
            "chunks_for_synthesis": len(unique_chunks)
        }
        
        processing_log.append({
            "phase": "operation_execution",
            "duration_seconds": (datetime.now() - phase_start).total_seconds(),
            "status": "completed",
            "summary": retrieval_summary,
            "execution_results": execution_results
        })
        
        return {
            "chunks": unique_chunks,
            "summary": retrieval_summary,
            "execution_results": execution_results
        }

    def _synthesis_phase(self, inputs: IntegratedDiscoverySynthesisInput,
                        retrieved_content: Dict, processing_log: List) -> Dict:
        """Phase 4: Process retrieved content through RefineSynthesisTool."""
        
        phase_start = datetime.now()
        
        chunks = retrieved_content["chunks"]
        
        if not chunks:
            synthesis_result = {
                "response": (
                    f"I could not find relevant content to answer your query: '{inputs.user_query}'. "
                    f"This may be because the search operations determined from your query and the available data "
                    f"did not return matching content, or the specific information you're looking for may not be "
                    f"present in the available documents."
                ),
                "metadata": {
                    "synthesis_performed": False,
                    "reason": "No relevant content chunks retrieved from determined operations"
                }
            }
        else:
            # Execute RefineSynthesisTool synthesis
            synthesis_result = self.synthesis_tool.refine_synthesis(
                user_query=inputs.user_query,
                chunks=chunks,
                prioritize=True
            )
        
        processing_log.append({
            "phase": "refine_synthesis",
            "duration_seconds": (datetime.now() - phase_start).total_seconds(),
            "status": "completed",
            "input_chunks": len(chunks),
            "synthesis_metadata": synthesis_result.get("metadata", {}),
            "synthesis_strategy": synthesis_result.get("metadata", {}).get("processing_strategy", "unknown")
        })
        
        return synthesis_result

    def _format_comprehensive_response(self, inputs: IntegratedDiscoverySynthesisInput,
                                     synthesis_result: Dict, processing_log: List,
                                     total_time: float, discovery_results: Dict,
                                     metadata_results: List, operations_plan: Dict) -> str:
        """Format the final comprehensive response with full transparency."""
        
        response_data = {
            "status": "SUCCESS",
            "user_query": inputs.user_query,
            "ai_response": synthesis_result.get("response", "No response generated"),
            "processing_summary": {
                "total_processing_time_seconds": total_time,
                "phases_completed": len(processing_log),
                "synthesis_performed": synthesis_result.get("metadata", {}).get("synthesis_performed", True),
                "total_chunks_processed": synthesis_result.get("metadata", {}).get("total_chunks", 0),
                "processing_strategy": operations_plan.get("strategy", "retrieval_synthesis"),
                "operations_executed": operations_plan.get("operation_determination", {}).get("selected_operations", operations_plan.get("operations", []))
            },
            "correct_flow_executed": {
                "step_1": "User Query + JSONSearchTool Discovery and Metadata Results",
                "step_2": "Intelligent Size-Based Processing Strategy Determination",
                "step_3": "Direct Synthesis (if <100k words) OR Targeted Retrieval + Refine Synthesis (if ≥100k words)",
                "step_4": "Comprehensive Response Generation with Processing Transparency"
            }
        }
        
        # Include detailed reasoning if requested
        if inputs.include_reasoning:
            response_data["detailed_reasoning"] = {
                "discovery_and_metadata_results": {
                    "discovery_results": discovery_results,
                    "metadata_results": metadata_results
                },
                "operation_determination_reasoning": operations_plan,
                "llm_decision_making_process": processing_log,
                "synthesis_metadata": synthesis_result.get("metadata", {}),
                "refine_synthesis_processing_log": synthesis_result.get("processing_log", [])
            }
        
        # Include configuration details
        response_data["configuration"] = {
            "json_file_path": inputs.json_file_path,
            "max_results": inputs.max_results,
            "synthesis_config": synthesis_result.get("config", {}),
            "tools_used": {
                "discovery_and_search": "JSONSearchTool",
                "synthesis": "RefineSynthesisTool"
            }
        }
        
        return json.dumps(response_data, indent=2, ensure_ascii=False)

    def _format_error_response(self, error_message: str, user_query: str) -> str:
        """Format error responses with helpful information."""
        
        error_response = {
            "status": "ERROR",
            "user_query": user_query,
            "error_message": error_message,
            "correct_flow": "User Query + JSONSearchTool (discovery and metadata results) → JSONSearchTool (operation/s) → RefineSynthesisTool → Comprehensive Response",
            "suggestions": [
                "Ensure the JSON file path exists and contains processed document data",
                "Verify that the Gemini API key is properly configured (set GEMINI_API_KEY environment variable)",
                "Check that your query is clear and contains searchable terms",
                "Ensure the unified_results.json file has been generated from your documents"
            ],
            "example_usage": {
                "user_query": "What are the capital requirements mentioned in the OSFI documents?",
                "json_file_path": "../Fetch_data/unified_results.json"
            }
        }
        
        return json.dumps(error_response, indent=2, ensure_ascii=False)

    async def _arun(self, **kwargs) -> str:
        """Async version of _run."""
        return self._run(**kwargs)


def create_integrated_discovery_synthesis_tool(json_file_path: str = "../Fetch_data/unified_results.json") -> IntegratedDiscoverySynthesisTool:
    """
    Factory function to create an IntegratedDiscoverySynthesisTool.
    
    Args:
        json_file_path: Path to the unified_results.json file
        
    Returns:
        Configured IntegratedDiscoverySynthesisTool instance
    """
    tool = IntegratedDiscoverySynthesisTool()
    return tool


if __name__ == "__main__":
    """Example usage demonstrating the correct flow."""
    
    print("🚀 LangChain Integrated Discovery and Synthesis Tool Demo")
    print("=" * 70)
    print("Correct Flow: User Query + JSONSearchTool (discovery and metadata) → JSONSearchTool (operations) → RefineSynthesisTool → Response")
    print("=" * 70)
    
    # Create the tool
    tool = create_integrated_discovery_synthesis_tool()
    
    # Example test queries
    test_queries = [
        {
            "user_query": "What are the key capital requirements for market risk according to OSFI?",
            "include_reasoning": True
        },
        {
            "user_query": "Show me the Balance Sheet data from the financial spreadsheet",
            "include_reasoning": True
        },
        {
            "user_query": "What regulatory frameworks are discussed in the available documents?",
            "include_reasoning": True
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test['user_query']}")
        print("-" * 50)
        
        try:
            result = tool._run(**test)
            result_data = json.loads(result)
            
            print(f"Status: {result_data['status']}")
            if result_data['status'] == 'SUCCESS':
                print(f"Response Preview: {result_data['ai_response'][:200]}...")
                print(f"Processing Time: {result_data['processing_summary']['total_processing_time_seconds']:.2f}s")
                print(f"Operations Executed: {len(result_data['processing_summary']['operations_executed'])}")
                print(f"Chunks Processed: {result_data['processing_summary']['total_chunks_processed']}")
                
                if test.get('include_reasoning'):
                    ops = result_data['processing_summary']['operations_executed']
                    print(f"Operations: {[op.get('operation', 'unknown') for op in ops]}")
            else:
                print(f"Error: {result_data['error_message']}")
                
        except Exception as e:
            print(f"Test failed: {str(e)}")
    
    print("\n✅ Demo complete!")
    print("\nUsage with LangChain agents:")
    print("""
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from integrated_discovery_synthesis_tool import create_integrated_discovery_synthesis_tool

# Create tool and agent
tool = create_integrated_discovery_synthesis_tool()
llm = OpenAI(temperature=0)

agent = initialize_agent(
    tools=[tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# The tool will automatically:
# 1. Use discovery + metadata to understand available data
# 2. Combine with user query to determine optimal operations  
# 3. Execute JSONSearchTool operations
# 4. Process through RefineSynthesisTool
response = agent.run("Analyze the capital requirements and provide a comprehensive summary")
""")