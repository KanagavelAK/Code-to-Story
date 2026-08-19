import os
import json
import time
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# System prompt for short/simple code (under 15 lines)
QUICK_PROMPT = """You are a creative coding teacher who explains code as a plain English story — like you are narrating a children's book, but for junior developers.

Rules you must follow:
1. Treat every function, variable, and loop as a character or action in the story
2. Use simple, everyday analogies — never technical jargon
3. Write in second or third person narrative style
4. Each logical step in the code becomes a sentence or short paragraph in the story
5. Make it memorable — use metaphors like doors, factories, chefs, post offices, security guards
6. Never use the words: iterate, instantiate, invoke, execute, runtime, implement
7. Keep total story under 200 words

Return ONLY a valid JSON object in this exact format:
{
  "story": "the full plain English story here",
  "summary": "one sentence — what this code does in plain English",
  "key_steps": ["step 1 in plain english", "step 2", "step 3"]
}
No markdown. No backticks. No explanation outside the JSON."""

# System prompt for complex code (15+ lines) — chapter-based storytelling
CHAPTER_PROMPT = """You are a creative coding teacher who explains code as a plain English story — like you are narrating a children's book with chapters, but for junior developers.

Rules you must follow:
1. Break the code into logical sections (each function, class, or block is a chapter)
2. Start each chapter with "Chapter N: [Title]" followed by its story
3. Use simple, everyday analogies — never technical jargon
4. Write in second or third person narrative style
5. Make it memorable — use metaphors like doors, factories, chefs, post offices, security guards
6. Never use the words: iterate, instantiate, invoke, execute, runtime, implement
7. Keep total story under 400 words

Return ONLY a valid JSON object in this exact format:
{
  "story": "Chapter 1: [Title]\\n[story]\\n\\nChapter 2: [Title]\\n[story]...",
  "summary": "one sentence — what this entire code does in plain English",
  "key_steps": ["step 1 in plain english", "step 2", "step 3", "step 4", "step 5"]
}
No markdown. No backticks. No explanation outside the JSON."""


def clean_json_response(response_text):
    """Strip thinking tags, markdown fences, and extract pure JSON."""
    import re

    # Strip Qwen3's <think>...</think> chain-of-thought block
    cleaned = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()

    # Strip markdown fences
    cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
    cleaned = cleaned.removeprefix("```").removesuffix("```").strip()

    # Extract JSON object between first { and last } as a safety net
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    return cleaned


def pick_prompt(code):
    """Choose quick or chapter prompt based on code complexity."""
    line_count = len([l for l in code.strip().splitlines() if l.strip()])
    return CHAPTER_PROMPT if line_count >= 15 else QUICK_PROMPT


def generate_story(code: str, language: str) -> dict:
    """Take a code block and language, return a story dict via Groq API with retries."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    system_prompt = pick_prompt(code)
    user_prompt = f"Here is a {language} code block. Convert it to a story:\n\n{code}"

    # Retry up to 3 times — LLM output is non-deterministic
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500,
            )
            raw_text = response.choices[0].message.content
        except Exception as e:
            # If rate limited or API fails, wait and try again
            time.sleep(2 * (attempt + 1))
            continue
        cleaned = clean_json_response(raw_text)

        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            continue

    # All retries exhausted — return graceful fallback
    return {
        "story": "Could not parse the story. Please try again.",
        "summary": "Parse error.",
        "key_steps": ["Try again with a simpler code block."],
    }
