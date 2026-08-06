import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def analyze_script(script_text):
    """Generates a single 4-second scene breakdown."""
    print("🤖 AI Director creating a 4-second micro-video scene...")
    
    system_instruction = (
        "You are a short-form video editor creating a 4-second micro video. "
        "Return EXACTLY 1 scene. "
        "The narration MUST be short (5 to 7 words maximum) so it lasts around 3 to 4 seconds when spoken. "
        "Return ONLY a JSON object with a 'scenes' array containing 1 scene object with keys: "
        "'narration' and 'search_query'."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Topic/Script:\n{script_text}"}
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    
    try:
        parsed = json.loads(chat_completion.choices[0].message.content)
        return parsed.get("scenes", [])
    except Exception as e:
        print(f"⚠️ Error parsing AI director output: {e}")
        return []