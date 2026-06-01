"""
LangChain agent for manufacturing analysis.
Orchestrates tool calling for natural language queries against manufacturing data.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

from src.analysis_tools import (
    calculate_cycle_times,
    find_bottleneck_process,
    find_delayed_jobs,
    summarise_by_machine,
    summarise_by_process,
    estimate_wip_location,
    generate_summary_statistics,
    generate_excel_report,
)


def load_llm(provider: str = None):
    """
    Load and return an LLM instance based on the configured provider.
    Routes to OpenAI, Anthropic, or Ollama based on environment configuration.
    
    Args:
        provider: LLM provider to use. If None, uses LLM_PROVIDER env var.
                 Options: "openai", "anthropic", "ollama"
        
    Returns:
        Initialized LLM instance
        
    Raises:
        ValueError: If provider is not supported or API keys are missing
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        return ChatOpenAI(api_key=api_key, model=model, temperature=0.5)
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        return ChatAnthropic(api_key=api_key, model=model, temperature=0.5)
    
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama2")
        return ChatOllama(base_url=base_url, model=model, temperature=0.5)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _create_analysis_tools(df: pd.DataFrame) -> List[Tool]:
    """
    Create LangChain Tool wrappers for all analysis functions.
    Each tool includes proper docstrings for the LLM to understand its purpose.
    
    Args:
        df: The cleaned manufacturing data DataFrame
        
    Returns:
        List of Tool objects
    """
    
    def _calculate_cycle_times_tool():
        """Calculate cycle time (in minutes) for each job in the dataset."""
        result_df = calculate_cycle_times(df)
        return {
            "status": "success",
            "message": f"Calculated cycle times for {len(result_df)} jobs",
            "data": result_df[["job_id", "process_step", "cycle_time_minutes"]].head(10).to_dict(orient="records")
        }
    
    def _find_bottleneck_tool():
        """Find the process step that is the bottleneck (longest average cycle time)."""
        result = find_bottleneck_process(df)
        return {
            "status": "success",
            "bottleneck": result["bottleneck_process"],
            "avg_cycle_time_minutes": result["avg_cycle_time"],
            "details": result
        }
    
    def _find_delayed_jobs_tool():
        """Identify jobs that are delayed (completed after due date or marked as late)."""
        result_df = find_delayed_jobs(df)
        if len(result_df) == 0:
            return {
                "status": "success",
                "message": "No delayed jobs found",
                "delayed_count": 0
            }
        return {
            "status": "success",
            "delayed_count": len(result_df),
            "data": result_df[["job_id", "process_step", "delay_reason"]].head(10).to_dict(orient="records")
        }
    
    def _machine_summary_tool():
        """Summarize job metrics and utilization by machine."""
        result = summarise_by_machine(df)
        return {
            "status": "success",
            "total_machines": result["total_machines"],
            "top_machines": result["top_machines"][:5],
            "underutilized_machines": result["underutilized"][:5]
        }
    
    def _process_summary_tool():
        """Summarize job metrics and cycle times by process step."""
        result = summarise_by_process(df)
        return {
            "status": "success",
            "by_cycle_time": result["by_cycle_time"][:5],
            "by_job_volume": result["by_job_volume"][:5]
        }
    
    def _wip_location_tool():
        """Estimate where work-in-progress (WIP) is concentrated in the production floor."""
        result = estimate_wip_location(df)
        return {
            "status": "success",
            "high_wip_locations": result["high_wip_locations"],
            "rationale": result["rationale"]
        }
    
    def _summary_statistics_tool():
        """Generate high-level summary statistics of the manufacturing data."""
        result = generate_summary_statistics(df)
        return {
            "status": "success",
            "data": result
        }
    
    # Create Tool objects
    tools = [
        Tool(
            name="calculate_cycle_times",
            func=_calculate_cycle_times_tool,
            description="Calculate cycle time (in minutes) for each manufacturing job"
        ),
        Tool(
            name="find_bottleneck_process",
            func=_find_bottleneck_tool,
            description="Find the process step that is the bottleneck (longest average cycle time)"
        ),
        Tool(
            name="find_delayed_jobs",
            func=_find_delayed_jobs_tool,
            description="Identify jobs that are delayed or completed after due date"
        ),
        Tool(
            name="summarise_by_machine",
            func=_machine_summary_tool,
            description="Summarize job metrics and machine utilization by equipment"
        ),
        Tool(
            name="summarise_by_process",
            func=_process_summary_tool,
            description="Summarize job metrics and cycle times by process step"
        ),
        Tool(
            name="estimate_wip_location",
            func=_wip_location_tool,
            description="Estimate where work-in-progress (WIP) is concentrated on the production floor"
        ),
        Tool(
            name="generate_summary_statistics",
            func=_summary_statistics_tool,
            description="Generate overall summary statistics of manufacturing performance"
        ),
    ]
    
    return tools


def run_agent(
    user_query: str,
    file_path: str,
    sheet_name: str,
    mapping: Dict[str, tuple],
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Run the LangChain agent to answer a user query about manufacturing data.
    
    Args:
        user_query: The user's natural language question
        file_path: Path to the Excel file (for context)
        sheet_name: Name of the sheet being analyzed
        mapping: Column mapping information
        df: The cleaned manufacturing DataFrame
        
    Returns:
        Dictionary with:
        - final_answer: LLM's response to the user query
        - tool_calls: List of tools that were invoked
        - intermediate_steps: Detailed step-by-step execution
        - summary_statistics: Key metrics (if generated)
        - bottleneck_analysis: Bottleneck info (if found)
    """
    
    try:
        # Load LLM
        llm = load_llm()
        
        # Create tools
        tools = _create_analysis_tools(df)
        
        # Create system prompt
        system_prompt = """You are an expert manufacturing analyst AI assistant.

Your role is to help users analyze manufacturing data and answer questions about:
- Production bottlenecks and cycle times
- Delayed jobs and scheduling issues
- Machine utilization and capacity
- Work-in-progress (WIP) locations and inventory
- Overall manufacturing performance metrics

Use the available tools to extract insights from the data.
When presenting findings, be specific with numbers and actionable insights.
Always explain WHY something is a problem and WHAT could be done about it.

Keep responses concise but informative. Format tables clearly.

File: {file_path}
Sheet: {sheet_name}
Records analyzed: {len(df)}
Mapped columns: {mapping}"""
        
        # Create prompt template using ReAct pattern
        prompt = PromptTemplate.from_template(
            system_prompt + "\n\nQuestion: {input}\n\nThought:"
        )
        
        # Create agent using ReAct - invoke directly
        agent = create_react_agent(llm, tools, prompt)
        
        # Run agent by invoking the runnable directly
        result = agent.invoke({"input": user_query})
        
        # Extract useful summary data if present
        summary_stats = None
        bottleneck_info = None
        
        try:
            summary_stats = generate_summary_statistics(df)
        except Exception:
            pass
        
        try:
            bottleneck_info = find_bottleneck_process(df)
        except Exception:
            pass
        
        # Parse result - handle both dict and string responses
        final_answer = result.get("output", "No response generated") if isinstance(result, dict) else str(result)
        
        return {
            "final_answer": final_answer,
            "tool_calls": [],
            "intermediate_steps": [],
            "summary_statistics": summary_stats,
            "bottleneck_analysis": bottleneck_info,
            "status": "success",
        }
    
    except Exception as e:
        return {
            "final_answer": f"Error: {str(e)}",
            "status": "error",
            "error_message": str(e),
        }