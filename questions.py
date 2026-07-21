"""
Question generation module.
Provides hardcoded fallback questions and AI-generated questions via Gemini API.
Uses the current google-genai SDK (not the deprecated google-generativeai).
"""

import json
import random
import os
import sys
from typing import List, Optional

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import google.genai (new SDK), fallback to hardcoded if not available
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from game_logic import LEVEL_RULES, LEVEL_MAPPING, DOMAINS


# ============================================================
# HARDCODED FALLBACK QUESTIONS
# ============================================================

HARDCODED_QUESTIONS = [
    # Level 1 - Medium, West Bengal focused
    {
        "question": "Which city is known as the 'City of Joy' in West Bengal?",
        "options": {"a": "Kolkata", "b": "Darjeeling", "c": "Siliguri", "d": "Howrah"},
        "correct": "a",
        "domain": "Geography",
        "level": 1,
    },
    {
        "question": "Who wrote the national anthem of India, 'Jana Gana Mana'?",
        "options": {"a": "Bankim Chandra Chattopadhyay", "b": "Rabindranath Tagore", "c": "Sarat Chandra Chattopadhyay", "d": "Michael Madhusudan Dutt"},
        "correct": "b",
        "domain": "Literature",
        "level": 1,
    },
    # Level 2 - Medium-hard, India focused
    {
        "question": "In which year did India gain independence from British rule?",
        "options": {"a": "1945", "b": "1946", "c": "1947", "d": "1948"},
        "correct": "c",
        "domain": "History",
        "level": 2,
    },
    {
        "question": "Which Indian cricketer is known as the 'God of Cricket'?",
        "options": {"a": "Virat Kohli", "b": "MS Dhoni", "c": "Sachin Tendulkar", "d": "Rahul Dravid"},
        "correct": "c",
        "domain": "Sports",
        "level": 2,
    },
    # Level 3 - Hard, Worldwide
    {
        "question": "What is the chemical symbol for the element Gold?",
        "options": {"a": "Go", "b": "Gd", "c": "Ag", "d": "Au"},
        "correct": "d",
        "domain": "Science",
        "level": 3,
    },
    {
        "question": "Who painted the Mona Lisa?",
        "options": {"a": "Michelangelo", "b": "Leonardo da Vinci", "c": "Raphael", "d": "Donatello"},
        "correct": "b",
        "domain": "Entertainment",
        "level": 3,
    },
    {
        "question": "What does 'HTTP' stand for in web addresses?",
        "options": {"a": "HyperText Transfer Protocol", "b": "HighText Transfer Path", "c": "HyperText Transmission Process", "d": "HostText Transfer Protocol"},
        "correct": "a",
        "domain": "Technology",
        "level": 3,
    },
    # Level 4 - Expert, Worldwide
    {
        "question": "Which planet in our solar system has the most moons?",
        "options": {"a": "Jupiter", "b": "Saturn", "c": "Uranus", "d": "Neptune"},
        "correct": "b",
        "domain": "Science",
        "level": 4,
    },
    {
        "question": "In which year did the Titanic sink?",
        "options": {"a": "1910", "b": "1911", "c": "1912", "d": "1913"},
        "correct": "c",
        "domain": "History",
        "level": 4,
    },
    {
        "question": "What is the capital city of Australia?",
        "options": {"a": "Sydney", "b": "Melbourne", "c": "Canberra", "d": "Brisbane"},
        "correct": "c",
        "domain": "Geography",
        "level": 4,
    },
    {
        "question": "Who wrote the play 'Romeo and Juliet'?",
        "options": {"a": "Christopher Marlowe", "b": "Ben Jonson", "c": "William Shakespeare", "d": "John Milton"},
        "correct": "c",
        "domain": "Literature",
        "level": 4,
    },
    # Level 5 - Extreme, Worldwide
    {
        "question": "What is the smallest country in the world by land area?",
        "options": {"a": "Monaco", "b": "Vatican City", "c": "San Marino", "d": "Liechtenstein"},
        "correct": "b",
        "domain": "Geography",
        "level": 5,
    },
    {
        "question": "Which element has the atomic number 1?",
        "options": {"a": "Helium", "b": "Oxygen", "c": "Hydrogen", "d": "Carbon"},
        "correct": "c",
        "domain": "Science",
        "level": 5,
    },
    {
        "question": "Who was the first person to walk on the moon?",
        "options": {"a": "Buzz Aldrin", "b": "Yuri Gagarin", "c": "Neil Armstrong", "d": "John Glenn"},
        "correct": "c",
        "domain": "Science",
        "level": 5,
    },
]


def get_hardcoded_questions() -> List[dict]:
    """Return the hardcoded fallback question set."""
    return [q.copy() for q in HARDCODED_QUESTIONS]


def get_hardcoded_questions_for_level(level: int, count: int) -> List[dict]:
    """Get hardcoded questions for a specific level."""
    level_questions = [q for q in HARDCODED_QUESTIONS if q["level"] == level]
    while len(level_questions) < count:
        level_questions.extend([q.copy() for q in level_questions[:count - len(level_questions)]])
    return level_questions[:count]


# ============================================================
# AI QUESTION GENERATION (NEW SDK: google-genai)
# ============================================================

# Current free-tier model as of 2026
# Use gemini-2.5-flash for best free-tier balance (10 RPM, 250K TPM)
# Fallback chain if that fails
gemini_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

SYSTEM_PROMPT = """You are a trivia question generator for a KBC-style quiz game.
Generate questions in strict JSON format only. No extra text, no markdown, no explanations.

Each question must follow this exact format:
{
  "question": "The question text here?",
  "options": {
    "a": "First option",
    "b": "Second option",
    "c": "Third option",
    "d": "Fourth option"
  },
  "correct": "a",
  "domain": "DomainName",
  "level": 1
}

Rules:
- The correct answer MUST be one of: a, b, c, d
- Exactly 4 options required
- Questions should be challenging but fair
- Do NOT repeat questions from common trivia sets
- Return ONLY a JSON array of questions, no other text
"""


def build_prompt(domain: str, difficulty: str, region: str, count: int, level: int) -> str:
    """Build the prompt for Gemini API."""
    if domain == "No Particular Domain":
        domain_text = "mixed topics across various domains"
    else:
        domain_text = f"the domain of {domain}"

    return f"""Generate {count} trivia questions for {domain_text}.

Difficulty: {difficulty}
Regional focus: {region}
Level: {level} (out of 5, where 5 is hardest)

Requirements:
- Each question must have exactly 4 options labeled a, b, c, d
- Only ONE option is correct
- The correct answer should be randomly distributed among a, b, c, d (not always 'a')
- Questions should be appropriate for the difficulty and region specified
- For West Bengal focus: include questions about Bengal culture, history, geography
- For India focus: include questions about Indian history, culture, sports, politics
- For worldwide: general knowledge from around the world
- Do not include any text outside the JSON array

Return format: a JSON array of {count} question objects."""


def validate_questions(questions: List[dict], expected_count: int) -> bool:
    """Validate that questions match the expected format."""
    if not isinstance(questions, list):
        return False
    if len(questions) != expected_count:
        return False

    for q in questions:
        if not all(k in q for k in ["question", "options", "correct", "domain", "level"]):
            return False
        if not all(k in q["options"] for k in ["a", "b", "c", "d"]):
            return False
        if q["correct"] not in ["a", "b", "c", "d"]:
            return False
        if not isinstance(q["question"], str) or len(q["question"]) < 10:
            return False

    return True


def generate_questions_ai(domain: str, difficulty: str, region: str, count: int, level: int, api_key: Optional[str] = None, _warned: list = None) -> List[dict]:
    """
    Generate questions using Gemini API with the new google-genai SDK.

    Args:
        domain: The domain for questions
        difficulty: Difficulty level string
        region: Regional focus string
        count: Number of questions to generate
        level: Level number (1-5)
        api_key: Gemini API key (optional, will try env var if not provided)

    Returns:
        List of question dictionaries
    """
    if _warned is None:
        _warned = []

    # === CHECK 1: Is google-genai installed? ===
    if not GENAI_AVAILABLE:
        if not _warned:
            print("⚠️  [CHECK 1] google-genai not installed. Using hardcoded questions.")
            print("   → Run: pip install google-genai")
            print("   → Or: pip install -r requirements.txt")
            _warned.append(True)
        return get_hardcoded_questions_for_level(level, count)

    # === CHECK 2: Is API key present? ===
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        if not _warned:
            print("⚠️  [CHECK 2] GEMINI_API_KEY not found. Using hardcoded fallback questions.")
            print("   → Create a .env file with: GEMINI_API_KEY=your_key_here")
            print("   → Or set environment variable: export GEMINI_API_KEY=your_key")
            print("   → Get a free key at: https://aistudio.google.com/app/apikey")
            _warned.append(True)
        return get_hardcoded_questions_for_level(level, count)

    # === CHECK 3: Try calling Gemini API ===
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(domain, difficulty, region, count, level)

    # Try each model in the fallback chain
    for model_name in gemini_models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[SYSTEM_PROMPT, prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=4000,
                    )
                )

                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                questions = json.loads(text)

                if validate_questions(questions, count):
                    for q in questions:
                        q["level"] = level
                    return questions
                else:
                    if not _warned:
                        print(f"⚠️  [CHECK 3] AI response format invalid for {model_name} (attempt {attempt + 1}). Retrying...")

            except Exception as e:
                error_msg = str(e).lower()
                if not _warned:
                    if "not found" in error_msg or "404" in error_msg:
                        print(f"⚠️  [CHECK 3] Model '{model_name}' not available. Trying next model...")
                    elif "api key not valid" in error_msg or "invalid" in error_msg:
                        print("❌ [CHECK 3] API key is invalid or expired.")
                        print("   → Your key may be wrong, revoked, or has no quota.")
                        print("   → Get a new key at: https://aistudio.google.com/app/apikey")
                        _warned.append(True)
                        return get_hardcoded_questions_for_level(level, count)
                    elif "quota" in error_msg or "exhausted" in error_msg or "429" in error_msg:
                        print("❌ [CHECK 3] API quota exceeded.")
                        print("   → Free tier has limits. Wait or use a different key.")
                        _warned.append(True)
                        return get_hardcoded_questions_for_level(level, count)
                    elif "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                        print(f"⚠️  [CHECK 3] Network error with {model_name}. Retrying...")
                    else:
                        print(f"⚠️  [CHECK 3] API error with {model_name}: {e}")

    if not _warned:
        print("⚠️  All API attempts failed. Using hardcoded fallback questions.")
        _warned.append(True)
    return get_hardcoded_questions_for_level(level, count)


def build_question_set_batch(domain: str, api_key: Optional[str] = None) -> List[dict]:
    """
    Build a complete 14-question set by batching API calls per level.
    This reduces API calls from 14 to 5.
    """
    all_questions = []
    warned = []

    for level in range(1, 6):
        rules = LEVEL_RULES[level]
        mapping = LEVEL_MAPPING[level]
        count = rules["question_count"]

        if domain == "No Particular Domain":
            actual_domain = "mixed topics across Science, History, Geography, Sports, Entertainment, Technology, and Literature"
        else:
            actual_domain = domain

        questions = generate_questions_ai(
            actual_domain, mapping["difficulty"], mapping["region"], count, level, api_key, _warned=warned
        )

        if questions and len(questions) >= count:
            all_questions.extend(questions[:count])
        else:
            all_questions.extend(get_hardcoded_questions_for_level(level, count))

    return all_questions


if __name__ == "__main__":
    print("Testing question generation...")
    print(f"Hardcoded questions available: {len(HARDCODED_QUESTIONS)}")
    print(f"google-genai SDK available: {GENAI_AVAILABLE}")

    questions = get_hardcoded_questions()
    print(f"\nHardcoded set: {len(questions)} questions")
    for q in questions[:3]:
        print(f"  [{q['level']}] {q['domain']}: {q['question'][:50]}...")
