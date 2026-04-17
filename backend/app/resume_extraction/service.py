import pymupdf4llm
import tempfile
import os
from langchain_core.prompts import PromptTemplate
from app.utils.llm_factory import get_gemini_model
from app.resume_extraction.schemas import ResumeExtractionResponse

def pdf_bytes_to_markdown(pdf_bytes: bytes) -> str:
    """
    Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.
    """
    try:
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        md_text = pymupdf4llm.to_markdown(tmp_path)
        return md_text
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def extract_structured_resume_data(markdown_text: str) -> ResumeExtractionResponse:
    """
    Feeds markdown to Gemini with strict structured output.
    """
    model = get_gemini_model(temperature=0.1)
    structured_llm = model.with_structured_output(ResumeExtractionResponse)

    prompt = PromptTemplate.from_template(
        """You are an expert technical recruiter and resume parser.
Extract the following information from the provided resume markdown into the required JSON structure.
Be concise but capture all relevant evidence for skills. Infer a 'headline' and 'summary' if missing.

RESUME MARKDOWN:
{resume_markdown}
"""
    )
    
    chain = prompt | structured_llm
    result: ResumeExtractionResponse = chain.invoke({"resume_markdown": markdown_text})
    return result
