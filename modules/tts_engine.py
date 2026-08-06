import edge_tts
import asyncio
import subprocess
import sys

SPEED_MAP = {
    "Extra Slow": "-30%",
    "Slow":       "-15%",
    "Normal":     "+0%",
    "Fast":       "+15%",
    "Extra Fast": "+30%",
}

def generate_voiceover(text, output_file, voice="en-US-ChristopherNeural", speed="Normal"):
    """Subprocess-based TTS — no asyncio conflict with Streamlit."""
    rate = SPEED_MAP.get(speed, "+0%")
    script = f"""
import asyncio, edge_tts
async def run():
    c = edge_tts.Communicate({repr(text)}, {repr(voice)}, rate={repr(rate)})
    await c.save({repr(output_file)})
asyncio.run(run())
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            timeout=60, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"⚠️ TTS error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⚠️ TTS timeout: {text[:50]}")
    except Exception as e:
        print(f"⚠️ TTS failed: {e}")