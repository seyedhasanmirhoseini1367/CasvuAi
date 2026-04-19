import re
import time
from groq import Groq, RateLimitError
from json_repair import repair_json
from config import GROQ_API_KEY, GROQ_MODEL

groq = Groq(api_key=GROQ_API_KEY)


def extract_json(text: str) -> str:
    """Extract and repair JSON from LLM response."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```\s*$", "", text).strip()

    # Find outermost { } by tracking depth
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    return repair_json(candidate)
    return repair_json(text)


def generate(prompt: str, retries: int = 5) -> str:
    """Call Groq with automatic retry on rate limit."""
    delay = 10
    for attempt in range(retries):
        try:
            response = groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return extract_json(response.choices[0].message.content)
        except RateLimitError:
            if attempt < retries - 1:
                print(f"  Rate limited - waiting {delay}s before retry...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
