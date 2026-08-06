import json
from groq import Groq

def analyze_script(script_text, api_key, scene_count=4, word_length="8 to 12 words"):
    """
    AI Director: Analyzes input script/topic and breaks it into structured scenes.
    
    Args:
        script_text (str): User's script or topic text.
        api_key (str): Groq API key passed from config or Streamlit secrets.
        scene_count (int): Total number of scenes to generate (e.g., 1, 4, 8).
        word_length (str): Target narration word count per scene.
        
    Returns:
        list: A list of dicts containing 'narration' and 'search_query'.
    """
    if not api_key:
        print("⚠️ Groq API key is missing.")
        return []

    client = Groq(api_key=api_key)

    system_instruction = (
        f"You are an expert film director and short-form video editor. "
        f"Break the user's script/topic into EXACTLY {scene_count} distinct scene(s). "
        f"Each scene narration MUST be roughly {word_length} long. "
        "For each scene, return: "
        "1. 'narration': Clear, engaging voiceover text. "
        "2. 'search_query': A simple, high-converting 1 to 3 word stock video search term. "
        f"Return ONLY a JSON object with a 'scenes' array containing {scene_count} scene object(s)."
    )

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Script / Topic:\n{script_text}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(chat_completion.choices[0].message.content)
        return parsed.get("scenes", [])
    except Exception as e:
        print(f"⚠️ AI Director script analysis error: {e}")
        return []