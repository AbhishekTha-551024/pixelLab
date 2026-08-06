import os

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# Voice Settings
VOICE = "en-US-ChristopherNeural"

# Directory Structure
OUTPUT_DIR = "output"
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- VIDEO RENDER SETTINGS ---
# For Fast Testing & Cloud Hosting (Recommended):
VIDEO_WIDTH = 1920   # 1080p Width
VIDEO_HEIGHT = 1080  # 1080p Height
DEFAULT_PRESET = "ultrafast"
DEFAULT_BITRATE = "8000k"

# For Local 4K Ultra HD Exports (Uncomment to enable):
# VIDEO_WIDTH = 3840
# VIDEO_HEIGHT = 2160
# DEFAULT_PRESET = "medium"
# DEFAULT_BITRATE = "35000k"