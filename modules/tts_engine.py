import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import edge_tts
from config import DEFAULT_VOICE

async def generate_voiceover(text, output_file, voice=DEFAULT_VOICE):
    """Generates an MP3 audio voiceover file using Edge-TTS."""
    if not text or not text.strip():
        return

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)