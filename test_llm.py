from openai import OpenAI
import sys

API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1"

try:
    client = OpenAI(api_key=API_KEY, base_url=API_URL)
    print("Testing Groq connection...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "test"}],
        timeout=5
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
