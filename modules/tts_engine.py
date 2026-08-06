import edge_tts
from config import DEFAULT_VOICE

async def generate_voiceover(text, output_file, voice=DEFAULT_VOICE):
    """
    Generates an MP3 audio voiceover file using Edge-TTS.
    
    Args:
        text (str): Narration sentence to synthesize.
        output_file (str): Absolute or relative path for the generated MP3 file.
        voice (str): Edge-TTS voice model name.
    """
    if not text or not text.strip():
        return

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)