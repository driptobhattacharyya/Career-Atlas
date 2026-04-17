from langchain_core.prompts import PromptTemplate
from app.utils.llm_factory import get_groq_model
from app.gap_analysis.schemas import GapAnalysisResponse

def generate_gaps_for_user(user_skills: list[str], target_role_skills: list[str], target_role_title: str) -> list:
    """
    Identifies missing skills based on a fast model comparing current vs required.
    """
    model = get_groq_model(model_name="llama3-70b-8192", temperature=0.2)
    structured_llm = model.with_structured_output(GapAnalysisResponse)
    
    prompt = PromptTemplate.from_template(
        """You are an expert career coach.
Given a user's CURRENT SKILLS and the POPULAR SKILLS for their TARGET ROLE, identify the 6 most impactful skill gaps preventing them from getting the job.

TARGET ROLE: {target_role}
TARGET ROLE EXPECTED SKILLS: {target_skills}

USER'S CURRENT SKILLS:
{user_skills}

Output a strictly nested JSON list of the top 6 gaps matching the final schema.
"""
    )
    
    chain = prompt | structured_llm
    result: GapAnalysisResponse = chain.invoke({
        "target_role": target_role_title,
        "target_skills": ", ".join(target_role_skills),
        "user_skills": ", ".join(user_skills)
    })
    
    return result.gaps
