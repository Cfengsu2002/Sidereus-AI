from typing import Any, List

from pydantic import BaseModel, Field  # Jason

class ResumeSection(BaseModel):
    index: int
    text: str

class ResumeParseResponse(BaseModel):
    filename: str
    page_count: int
    raw_text: str
    cleaned_text: str
    sections: List[ResumeSection]
    ai_result: dict[str, Any] | None = None


class JobMatchResponse(BaseModel):
    filename: str
    page_count: int
    job_description: str
    jd_keywords: list[str]
    resume_keywords: list[str]
    keyword_overlap: list[str]
    skill_match_rate: float = Field(..., ge=0.0, le=1.0)
    experience_relevance: float = Field(..., ge=0.0, le=1.0)
    education_relevance: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=100.0)
    summary: str


class ResumeAnalyzeResponse(BaseModel):
    filename: str
    page_count: int
    job_description: str
    parse: ResumeParseResponse
    match: JobMatchResponse

# the structure of the resume and the response