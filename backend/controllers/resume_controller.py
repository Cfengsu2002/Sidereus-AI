from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.schemas.resume_schema import (
    JobMatchResponse,
    ResumeAnalyzeResponse,
    ResumeParseResponse,
    ResumeSection,
)
from backend.services.llm_service import analyze_resume_with_llm
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.scores_service import compute_job_match

router = APIRouter(prefix="/api/v1", tags=["resume"])


def clean_resume_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return "\n".join(lines)


def split_into_sections(cleaned_text: str) -> list[ResumeSection]:
    lines = [line for line in cleaned_text.splitlines() if line.strip()]
    return [ResumeSection(index=index + 1, text=line) for index, line in enumerate(lines[:30])]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        raw_text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cleaned_text = clean_resume_text(raw_text)
    sections = split_into_sections(cleaned_text)
    try:
        ai_result = analyze_resume_with_llm(cleaned_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {exc}") from exc

    return ResumeParseResponse(
        filename=file.filename,
        page_count=page_count,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        sections=sections,
        ai_result=ai_result,
    )


@router.post("/resume/match", response_model=JobMatchResponse)
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> JobMatchResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        _raw_text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cleaned_text = clean_resume_text(_raw_text)
    try:
        ai_result = analyze_resume_with_llm(cleaned_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {exc}") from exc

    try:
        match_payload = compute_job_match(
            filename=file.filename,
            page_count=page_count,
            job_description=job_description,
            cleaned_text=cleaned_text,
            resume_structured=ai_result,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Match scoring failed: {exc}") from exc

    return JobMatchResponse.model_validate(match_payload)


@router.post("/resume/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> ResumeAnalyzeResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    jd = job_description.strip()
    if len(jd) < 20:
        raise HTTPException(status_code=400, detail="job_description must be at least 20 characters")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        raw_text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cleaned_text = clean_resume_text(raw_text)
    try:
        ai_result = analyze_resume_with_llm(cleaned_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {exc}") from exc

    sections = split_into_sections(cleaned_text)
    parse_payload = ResumeParseResponse(
        filename=file.filename,
        page_count=page_count,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        sections=sections,
        ai_result=ai_result,
    )

    try:
        match_payload = compute_job_match(
            filename=file.filename,
            page_count=page_count,
            job_description=jd,
            cleaned_text=cleaned_text,
            resume_structured=ai_result,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Match scoring failed: {exc}") from exc

    match_model = JobMatchResponse.model_validate(match_payload)

    return ResumeAnalyzeResponse(
        filename=file.filename,
        page_count=page_count,
        job_description=jd,
        parse=parse_payload,
        match=match_model,
    )
