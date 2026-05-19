from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from app.utils.llm_factory import get_gemini_model, get_groq_model
from app.job_hunter.tools import search_web
from app.job_hunter.schemas import ScrapedJobsResponse

class JobSearchState(TypedDict):
    target_role: str
    user_skills: list[str]
    location: str
    raw_results: list[dict]
    parsed_jobs: list[dict]
    iterations: int

def generate_search_queries(state: JobSearchState):
    """Generates optimal search queries to find job listings."""
    # We just create straightforward queries here based on the constraints
    queries = [
        f"'{state['target_role']}' job {state['location']} site:linkedin.com/jobs",
        f"entry level {state['target_role']} remote jobs",
        f"hiring {state['target_role']} {state['location']} greenhouse.io"
    ]
    return {**state, "raw_results": [], "parsed_jobs": [], "iterations": state.get("iterations", 0) + 1}

def execute_search(state: JobSearchState):
    """Executes search using Tavily (recency-filtered to the last month)."""
    role = state['target_role']
    loc = state['location']
    search_query = f"{role} jobs recent {loc}"
    results = search_web(search_query)
    return {**state, "raw_results": results}

def extract_and_score_jobs(state: JobSearchState):
    """Uses LLM to parse raw search results into JobMatchSchema structures."""
    model = get_groq_model(temperature=0.1)
    structured_llm = model.with_structured_output(ScrapedJobsResponse)
    
    prompt = PromptTemplate.from_template(
        """You are a job scraper that turns raw search results into structured Job Matching objects.
Compare the job descriptions to the USER SKILLS to determine Match Percentage, Matched keywords, and Missing Keywords.
Make sure Seniority is standardized.

USER SKILLS: {user_skills}
TARGET ROLE: {target_role}

RAW SEARCH TEXT:
{raw_results}
"""
    )
    
    combined_raw_text = "\\n".join([f"Url: {r.get('url')} Content: {r.get('content')}" for r in state['raw_results'][:5]])
    
    response: ScrapedJobsResponse = (prompt | structured_llm).invoke({
        "user_skills": ", ".join(state['user_skills']),
        "target_role": state['target_role'],
        "raw_results": combined_raw_text
    })
    
    return {**state, "parsed_jobs": response.jobs}

def should_continue(state: JobSearchState) -> str:
    if state["iterations"] >= 1 or len(state["parsed_jobs"]) >= 3:
        return "end"
    return "search"

# Build Graph
graph_builder = StateGraph(JobSearchState)

graph_builder.add_node("plan", generate_search_queries)
graph_builder.add_node("search", execute_search)
graph_builder.add_node("extract", extract_and_score_jobs)

graph_builder.set_entry_point("plan")
graph_builder.add_edge("plan", "search")
graph_builder.add_edge("search", "extract")
graph_builder.add_conditional_edges(
    "extract",
    should_continue,
    {"search": "search", "end": END}
)

job_hunter_agent = graph_builder.compile()
