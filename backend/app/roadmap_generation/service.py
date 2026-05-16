from langchain_core.prompts import PromptTemplate
from app.utils.llm_factory import get_groq_model
from app.roadmap_generation.schemas import RoadmapGenerationResponse

def create_roadmap_for_gaps(skill_gaps: list[dict], target_role_title: str) -> list:
    """
    Constructs an actionable learning roadmap based on identified skill gaps.
    """
    model = get_groq_model(temperature=0.2)
    structured_llm = model.with_structured_output(RoadmapGenerationResponse)
    
    gaps_str = "\n".join([f"- {g['skill']} ({g['category']}) - Prereqs: {g['prerequisites']}" for g in skill_gaps])
    
    prompt = PromptTemplate.from_template(
        """You are a senior mentor guiding a student toward a {target_role} role.
Based on their identified SKILL GAPS, generate a phased, week-by-week learning roadmap. Ensure prerequisites are placed in earlier phases.

SKILL GAPS:
{gaps_str}

For each gap, create a milestone containing course recommendations, a mini-project, and a checklist. Generate exactly {num_gaps} milestones.
"""
    )
    
    chain = prompt | structured_llm
    result: RoadmapGenerationResponse = chain.invoke({
        "target_role": target_role_title,
        "gaps_str": gaps_str,
        "num_gaps": len(skill_gaps)
    })
    
    return result.milestones
