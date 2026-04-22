"""
Module 3: JD keyword extraction + AI match scoring (OpenAI).
Primary inputs: cleaned resume text + job description text.

No caching — each request recomputes match scores.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _ai_match_and_score(
    *,
    job_description: str,
    cleaned_text: str,
    resume_structured: dict[str, Any] | None,
) -> dict[str, Any]:
    client = _get_client()
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "jd_keywords": {"type": "array", "items": {"type": "string"}},
            "resume_keywords": {"type": "array", "items": {"type": "string"}},
            "keyword_overlap": {"type": "array", "items": {"type": "string"}},
            "skill_match_rate": {"type": "number", "minimum": 0, "maximum": 1},
            "experience_relevance": {"type": "number", "minimum": 0, "maximum": 1},
            "education_relevance": {"type": "number", "minimum": 0, "maximum": 1},
            "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
            "summary": {"type": "string"},
        },
        "required": [
            "jd_keywords",
            "resume_keywords",
            "keyword_overlap",
            "skill_match_rate",
            "experience_relevance",
            "education_relevance",
            "overall_score",
            "summary",
        ],
    }
    payload = {
        "job_description": job_description,
        "cleaned_resume_text": cleaned_text[:14000],
        "resume_structured_hint": resume_structured or {},
    }
    response = client.responses.create(
        model=_OPENAI_MODEL,
        instructions=(
            "You are an expert technical recruiter. "
            "Extract important keywords from the job description and from the resume text. "
            "Score how well the candidate matches the job using ONLY evidence from "
            "cleaned_resume_text and job_description. "
            "resume_structured_hint may help disambiguate, but must not introduce facts "
            "that contradict cleaned_resume_text. "
            "Do not invent credentials, employers, or skills not supported by the resume. "
            "Return ONLY JSON matching the schema. No markdown. No extra keys."
        ),
        input=json.dumps(payload, ensure_ascii=False),
        text={"format": {"type": "json_schema", "name": "job_match_ai", "schema": schema}},
    )
    return json.loads(response.output_text)


def compute_job_match(
    *,
    filename: str,
    page_count: int,
    job_description: str,
    cleaned_text: str,
    resume_structured: dict[str, Any] | None = None,
) -> dict[str, Any]:
    jd = job_description.strip()
    if len(jd) < 20:
        raise ValueError("job_description must be at least 20 characters")

    match = _ai_match_and_score(
        job_description=jd,
        cleaned_text=cleaned_text,
        resume_structured=resume_structured,
    )

    return {
        "filename": filename,
        "page_count": page_count,
        "job_description": jd,
        "jd_keywords": match["jd_keywords"],
        "resume_keywords": match["resume_keywords"],
        "keyword_overlap": match["keyword_overlap"],
        "skill_match_rate": match["skill_match_rate"],
        "experience_relevance": match["experience_relevance"],
        "education_relevance": match["education_relevance"],
        "overall_score": match["overall_score"],
        "summary": match["summary"],
    }
