import os
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = (
    "You are roleplaying as an employee inside a strange, fictional company. "
    "Write natural workplace communication grounded in the supplied character "
    "details. Be specific, concise, and a little human. Return only the requested text."
)


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-5.6-luna"


def generate_text(prompt, model=None):
    """Generate text through OpenRouter, with a useful local-mode fallback."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return (
            "[AI is offline] Add OPENROUTER_API_KEY to your environment, then try this "
            "simulation again. The rest of OurTeam works without it."
        )

    payload = json.dumps({
        "model": model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 300,
    }).encode("utf-8")
    request = Request(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "OurTeam",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            completion = json.load(response)
        return completion["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "[AI is unavailable] OpenRouter could not generate a response. Please try again."
