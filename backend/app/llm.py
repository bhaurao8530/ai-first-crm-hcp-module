import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-120b").strip()


def call_groq(messages, model_name):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        },
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]


def _fallback_text(prompt: str, system: str = None) -> str:
    if system and "Respond ONLY with JSON" in system:
        return '{"intent":"chitchat","interaction_id":null,"follow_up_date":null}'
    if system and "Write a short, warm, professional confirmation reply" in system:
        return "Thanks for the update. I’ve noted your message and I’m ready to help with the next step."
    return "Thanks for the update. I’m ready to help with your CRM workflow."


def safe_invoke(prompt: str, system: str = None, json_mode: bool = False) -> str:
    """Calls Groq with the primary model, falling back to the secondary
    model if the call fails for any reason. Returns a helpful fallback when
    the LLM service is unavailable."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_err = None
    for model_name in [GROQ_MODEL, GROQ_FALLBACK_MODEL]:
        try:
            return call_groq(messages, model_name)
        except Exception as e:
            last_err = e
            continue

    return _fallback_text(prompt, system)


def extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from LLM output that may be
    wrapped in markdown fences or extra prose."""
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        text = text.replace("json", "", 1).strip() if text.lower().startswith("json") else text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except Exception:
        return {}
