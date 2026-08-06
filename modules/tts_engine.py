import edge_tts
from config import VOICE

async def generate_voiceover(text, output_file):
    """Generates an MP3 voiceover file for a given text snippet."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)