import edge_tts
import asyncio
import subprocess
import sys
from config import VOICE

def generate_voiceover(text, output_file):
    """
    TTS engine — Python 3.14 + Streamlit Cloud compatible.
    
    nest_asyncio use NAHI karte (Streamlit Cloud pe crash karta hai).
    Subprocess mein fresh Python process spawn karte hain — 
    completely isolated event loop milta hai, koi conflict nahi.
    """
    # Inline Python script jo subprocess mein run hoga
    script = f"""
import asyncio
import edge_tts

async def run():
    communicate = edge_tts.Communicate({repr(text)}, {repr(VOICE)})
    await communicate.save({repr(output_file)})

asyncio.run(run())
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            timeout=60,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"⚠️ TTS subprocess error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⚠️ TTS timeout for text: {text[:50]}...")
    except Exception as e:
        print(f"⚠️ TTS generation failed: {e}")