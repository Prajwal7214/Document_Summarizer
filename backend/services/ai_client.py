import time
import os
from fastapi import HTTPException
from config import settings


def call_gemini(prompt: str) -> str:
    """
    Call Google Gemini via the google-generativeai SDK.
    Used as primary AI provider (API key in .env).
    """
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text


def call_groq(prompt: str) -> str:
    """
    Call Groq cloud API as secondary fallback.
    """
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a document analysis expert. Always respond with valid JSON only. No markdown, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=2048,
        temperature=0.1,
    )
    return chat.choices[0].message.content


def call_ollama(prompt: str) -> str:
    """
    Call local Ollama AI (tertiary fallback — requires Ollama running locally).
    """
    import ollama
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a document analysis expert. Always respond with valid JSON only. No markdown, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response["message"]["content"]


def call_ai_with_fallback(prompt: str) -> str:
    """
    Try AI providers in order: Gemini → Groq → Ollama.
    Returns the first successful response.
    Raises HTTPException(500) only if all providers fail.
    """
    errors = []

    # 1️⃣ Try Gemini first (fastest, cloud, API key in .env)
    if settings.GEMINI_API_KEY:
        try:
            print("Calling Gemini...")
            result = call_gemini(prompt)
            print("Gemini responded successfully.")
            return result
        except Exception as e:
            print(f"Gemini failed: {e}")
            errors.append(f"Gemini: {str(e)}")
    else:
        errors.append("Gemini: no API key configured")

    # 2️⃣ Try Groq as first fallback
    if settings.GROQ_API_KEY:
        try:
            print("Calling Groq...")
            result = call_groq(prompt)
            print("Groq responded successfully.")
            return result
        except Exception as e:
            print(f"Groq failed: {e}")
            errors.append(f"Groq: {str(e)}")
    else:
        errors.append("Groq: no API key configured")

    # 3️⃣ Try local Ollama as last resort
    for attempt in range(2):
        try:
            print(f"Calling Ollama locally (attempt {attempt + 1})...")
            result = call_ollama(prompt)
            print("Ollama responded successfully.")
            return result
        except Exception as e:
            error_msg = str(e).lower()
            if ("connection" in error_msg or "refused" in error_msg) and attempt == 0:
                print("Ollama not ready, retrying in 3s...")
                time.sleep(3)
                continue
            errors.append(f"Ollama: {str(e)}")
            break

    # All providers failed
    raise HTTPException(
        status_code=500,
        detail=f"All AI providers failed. Details: {' | '.join(errors)}"
    )