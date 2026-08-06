import edge_tts
import asyncio
import nest_asyncio
from config import VOICE

# ✅ FIX #2 (Part A): nest_asyncio allows asyncio.run() inside Streamlit's existing event loop
nest_asyncio.apply()

async def _generate_voiceover_async(text, output_file):
    """Internal async function to generate voiceover."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def generate_voiceover(text, output_file):
    """
    ✅ FIX #2 (Part B): Synchronous wrapper — no more asyncio.run() inside compositor.
    Streamlit ke andar nested event loop crash ab nahi hoga.
    """
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_generate_voiceover_async(text, output_file))
    except RuntimeError:
        # Fallback: new loop banao agar existing loop closed ho
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_voiceover_async(text, output_file))