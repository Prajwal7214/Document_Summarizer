import sys
sys.path.insert(0, '.')
from config import settings

print("GEMINI_API_KEY present:", bool(settings.GEMINI_API_KEY))
print("GROQ_API_KEY present:", bool(settings.GROQ_API_KEY))
print("GEMINI_MODEL:", settings.GEMINI_MODEL)

prompt = 'Output ONLY this JSON, nothing else: {"title": "Test", "summary": "This is a test.", "bullets": ["point 1"], "highlights": ["highlight 1"], "keywords": ["test"]}'

# Test Gemini
try:
    from services.ai_client import call_gemini
    result = call_gemini(prompt)
    print("\n--- GEMINI RESPONSE ---")
    print(result[:500])
except Exception as e:
    print(f"\nGemini FAILED: {e}")

# Test Groq
try:
    from services.ai_client import call_groq
    result = call_groq(prompt)
    print("\n--- GROQ RESPONSE ---")
    print(result[:500])
except Exception as e:
    print(f"\nGroq FAILED: {e}")
