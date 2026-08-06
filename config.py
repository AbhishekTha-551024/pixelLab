import os

# API Keys - Load from environment or Streamlit secrets only
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")  # ✅ FIX #3: Hardcoded key hata diya

# Voice Settings
VOICE = "en-US-ChristopherNeural"

# Directory Structure
OUTPUT_DIR = "output"
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- VIDEO RENDER SETTINGS ---
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 720
DEFAULT_PRESET = "ultrafast"
DEFAULT_BITRATE = "8000k"
FPS = 24