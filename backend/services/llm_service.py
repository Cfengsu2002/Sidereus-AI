import json
import os

from openai import OpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def build_input_text(raw_text: str) -> str:
    return f"""
Process the following resume text extracted from a PDF.

Tasks:
1. Clean the text:
- remove duplicated spaces
- remove obvious PDF extraction noise
- remove repeated headers or footers if present
- fix broken line breaks when appropriate
- preserve all meaningful content
- do not change the meaning
- do not invent information

2. Split the cleaned text into logical sections.
Each section must contain:
- title
- content

3. Extract the following information from the cleaned text only:
Basic Information (required):
- name
- phone
- email
- address

Job Information (optional):
- job_intention
- expected_salary

Background Information (optional):
- years_of_experience
  * include internships, part-time, and full-time experience
  * return a readable value like "about 2 years" or "1.5 years"
- education_background
  * return as a list of strings
- project_experience
  * return as a list of strings

Important:
- If a field is missing, return an empty string or empty list
- Do not guess
- Keep the output concise and structured

Resume text:
{raw_text}
""".strip()


def analyze_resume_with_llm(raw_text: str) -> dict:
    client = _get_client()
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are an AI resume parser. "
            "Return ONLY data matching the provided JSON schema. "
            "Do not include markdown. "
            "Do not include explanations. "
            "Do not add extra keys."
        ),
        input=build_input_text(raw_text),
        text={
            "format": {
                "type": "json_schema",
                "name": "resume_parse_result",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "cleaned_text": {
                            "type": "string"
                        },
                        "sections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["title", "content"]
                            }
                        },
                        "basic_info": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "phone": {"type": "string"},
                                "email": {"type": "string"},
                                "address": {"type": "string"}
                            },
                            "required": ["name", "phone", "email", "address"]
                        },
                        "job_info": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "job_intention": {"type": "string"},
                                "expected_salary": {"type": "string"}
                            },
                            "required": ["job_intention", "expected_salary"]
                        },
                        "background_info": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "years_of_experience": {"type": "string"},
                                "education_background": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "project_experience": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": [
                                "years_of_experience",
                                "education_background",
                                "project_experience"
                            ]
                        }
                    },
                    "required": [
                        "cleaned_text",
                        "sections",
                        "basic_info",
                        "job_info",
                        "background_info"
                    ]
                }
            }
        },
    )
    return json.loads(response.output_text)