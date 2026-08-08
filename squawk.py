import os


SYSTEM_PROMPT = (
    "You are roleplaying as an employee inside a strange, fictional company. "
    "Write natural workplace communication grounded in the supplied character "
    "details. Be specific, concise, and a little human. Return only the requested text."
)


def generate_text(prompt, engine=None):
    """Generate text when an API key exists, with a useful local-mode fallback."""
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "[AI is offline] Add OPENAI_API_KEY to your environment, then try this "
            "simulation again. The rest of OurTeam works without it."
        )

    # Import lazily so the entire sandbox still runs without the optional AI client.
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=engine or os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        instructions=SYSTEM_PROMPT,
        input=prompt,
        max_output_tokens=300,
    )
    return response.output_text.strip()
