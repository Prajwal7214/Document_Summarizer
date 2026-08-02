import json
import re
from config import settings
from services.file_parser import chunk_text
from services.ai_client import call_ai_with_fallback
from services.cache_service import get_cached, set_cache
import asyncio


# ── Prompts ────────────────────────────────────────────────────────────────────

SHORT_PROMPT = """You are a JSON generator. Output ONLY a JSON object, nothing else.
No explanations. No markdown. No code fences. Just pure JSON.

Output this exact structure:
{{
  "title": "document title here",
  "summary": "one sentence summary here",
  "bullets": [
    "key point 1",
    "key point 2",
    "key point 3"
  ],
  "highlights": [
    "most important sentence from document"
  ],
  "keywords": ["word1", "word2", "word3", "word4", "word5"]
}}

Rules:
- bullets: exactly 3 items
- highlights: exactly 1 sentence copied verbatim from document
- keywords: exactly 5 lowercase words
- summary: ONE sentence only
- Output ONLY the JSON, nothing before or after

Document text:
---
{document_text}
---

JSON output:"""


DETAILED_PROMPT = """You are a JSON generator. Output ONLY a JSON object, nothing else.
No explanations. No markdown. No code fences. Just pure JSON.

Output this exact structure:
{{
  "title": "document title here",
  "summary": "5 to 7 sentence detailed paragraph here",
  "bullets": [
    "detailed point 1",
    "detailed point 2",
    "detailed point 3",
    "detailed point 4",
    "detailed point 5"
  ],
  "highlights": [
    "most important sentence from document",
    "second most important sentence",
    "third most important sentence"
  ],
  "keywords": ["word1", "word2", "word3", "word4", "word5"]
}}

Rules:
- bullets: exactly 5 detailed items
- highlights: exactly 3 sentences copied verbatim from document
- keywords: exactly 5 lowercase words
- summary: 5 to 7 sentences
- Output ONLY the JSON, nothing before or after

Document text:
---
{document_text}
---

JSON output:"""


ACADEMIC_PROMPT = """You are a JSON generator. Output ONLY a JSON object, nothing else.
No explanations. No markdown. No code fences. Just pure JSON.

Output this exact structure:
{{
  "title": "formal academic title here",
  "summary": "formal abstract style summary in 5 to 6 sentences covering background objective methodology findings conclusions",
  "bullets": [
    "Objective: statement of purpose",
    "Methodology: approach used",
    "Finding 1: specific result",
    "Finding 2: specific result",
    "Implication: broader impact"
  ],
  "highlights": [
    "most significant claim quoted verbatim",
    "key methodological statement quoted verbatim",
    "primary conclusion quoted verbatim"
  ],
  "keywords": ["word1", "word2", "word3", "word4", "word5"]
}}

Rules:
- bullets: exactly 5 items with labels
- highlights: exactly 3 sentences copied verbatim from document
- keywords: exactly 5 lowercase academic terms
- summary: formal academic tone
- Output ONLY the JSON, nothing before or after

Document text:
---
{document_text}
---

JSON output:"""


PROMPTS = {
    "short": SHORT_PROMPT,
    "detailed": DETAILED_PROMPT,
    "academic": ACADEMIC_PROMPT,
}


def build_prompt(document_text: str, summary_type: str = "detailed") -> str:
    """Build prompt using smart chunking."""
    chunks = chunk_text(document_text)
    text_to_use = chunks[0]
    if len(chunks) > 1:
        text_to_use = chunks[0] + "\n\n[...]\n\n" + document_text[-500:]
    return PROMPTS.get(summary_type, DETAILED_PROMPT).format(document_text=text_to_use)


def parse_response(raw_text: str) -> dict:
    """
    Smartly parse JSON from AI response.
    Handles common issues from local Ollama models.
    """
    cleaned = raw_text.strip()

    # Remove markdown code fences
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            if part.startswith("json"):
                cleaned = part[4:].strip()
                break
            elif "{" in part:
                cleaned = part.strip()
                break

    # Extract only the JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    # Fix common JSON issues from local models
    cleaned = re.sub(r',\s*}', '}', cleaned)   # trailing commas in objects
    cleaned = re.sub(r',\s*]', ']', cleaned)   # trailing commas in arrays

    # Fix smart quotes but ONLY if they are outside string values, or just let json.loads handle them.
    # Actually, json.loads requires standard double quotes for keys and string enclosures.
    # Replacing all smart quotes corrupts strings that legitimately contain them.
    # A safer approach is to only replace smart quotes that look like they enclose strings.
    cleaned = re.sub(r'[\u201c\u201d]', '"', cleaned)
    cleaned = re.sub(r'[\u2018\u2019]', "'", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to fix truncated JSON
        try:
            open_braces = cleaned.count("{") - cleaned.count("}")
            open_brackets = cleaned.count("[") - cleaned.count("]")
            cleaned += "]" * open_brackets + "}" * open_braces
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # If all parsing attempts fail, return an empty dict.
            # The router will catch the validation error and provide graceful fallbacks.
            print(f"[ERROR] AI returned malformed JSON that could not be repaired.")
            return {}


async def summarize_document(text: str, summary_type: str = "detailed") -> dict:
    """Single document summarization with cache."""
    # Check cache first
    cached = await get_cached(text, summary_type)
    if cached:
        return cached

    prompt = build_prompt(text, summary_type)
    raw_text = await call_ai_with_fallback(prompt)
    result = parse_response(raw_text)

    if result:
        await set_cache(text, summary_type, result)
    return result


async def summarize_single_for_multi(
    filename: str,
    text: str,
    summary_type: str = "detailed"
) -> dict:
    """Summarize one document as part of multi-document batch."""
    # Check cache first
    cached = await get_cached(text, summary_type)
    if cached:
        result = cached.copy()
        result["name"] = filename
        return result

    prompt = build_prompt(text, summary_type)
    raw_text = await call_ai_with_fallback(prompt)
    result = parse_response(raw_text)

    if result:
        await set_cache(text, summary_type, result)
    result["name"] = filename
    return result