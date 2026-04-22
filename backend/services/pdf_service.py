import io
from pypdf import PdfReader
def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    all_text: list[str] = []
    page_count = 0
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        page_count = len(reader.pages)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text.append(text.strip())
        raw_text = "\n\n".join(all_text).strip()
        return raw_text, page_count
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")