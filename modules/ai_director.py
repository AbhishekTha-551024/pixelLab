import json
from groq import Groq

TONE_PROMPTS = {
    "Cinematic & Epic":   "Use powerful, dramatic language. Build tension and awe.",
    "Documentary":        "Use factual, informative, and measured tone.",
    "Motivational":       "Use inspiring, energetic, action-driven language.",
    "News Style":         "Use clear, objective, journalistic tone.",
    "Story Narrative":    "Use storytelling with characters and emotion.",
    "Educational":        "Use simple, clear, explanatory language.",
    "Dramatic":           "Use emotional, high-stakes, suspenseful language.",
}

LANG_PROMPTS = {
    "English":   "Write in English.",
    "Hindi":     "Write in Hindi (Devanagari script).",
    "Hinglish":  "Write in Hinglish (mix of Hindi and English).",
    "Spanish":   "Write in Spanish.",
    "French":    "Write in French.",
    "German":    "Write in German.",
    "Arabic":    "Write in Arabic.",
}

def analyze_script(script_text, api_key, scene_count=4, word_length="8 to 12 words",
                   tone="Cinematic & Epic", language="English"):
    if not api_key:
        print("⚠️ Groq API key missing.")
        return []

    client = Groq(api_key=api_key)

    tone_instruction = TONE_PROMPTS.get(tone, "")
    lang_instruction = LANG_PROMPTS.get(language, "Write in English.")

    system_instruction = (
        f"You are an expert film director and short-form video editor. "
        f"Break the user's script/topic into EXACTLY {scene_count} distinct scene(s). "
        f"Each scene narration MUST be roughly {word_length} long. "
        f"Tone: {tone_instruction} "
        f"Language: {lang_instruction} "
        "For each scene return: "
        "1. 'narration': Clear, engaging voiceover text. "
        "2. 'search_query': A simple 1-3 word English stock video search term (always English regardless of language). "
        f"Return ONLY a JSON object with a 'scenes' array containing {scene_count} objects."
    )

    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user",   "content": f"Script / Topic:\n{script_text}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        parsed = json.loads(chat.choices[0].message.content)
        return parsed.get("scenes", [])
    except Exception as e:
        print(f"⚠️ AI Director error: {e}")
        return []