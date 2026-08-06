import os
import streamlit as st
from config import GROQ_API_KEY, PIXABAY_API_KEY, OUTPUT_DIR
from modules.ai_director import analyze_script
from modules.compositor import build_master_video

# ❌ nest_asyncio bilkul nahi — Python 3.14 + Streamlit Cloud pe crash karta hai

# --- STREAMLIT PAGE SETUP ---
st.set_page_config(
    page_title="Pixelab - AI Video Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Pixelab - AI Video Generator")
st.caption("Generate cinematic HD short videos with custom subtitles and AI voiceover.")

# --- API KEY RESOLUTION ---
active_groq_key = GROQ_API_KEY
active_pixabay_key = PIXABAY_API_KEY

if "GROQ_API_KEY" in st.secrets:
    active_groq_key = st.secrets["GROQ_API_KEY"]
if "PIXABAY_API_KEY" in st.secrets:
    active_pixabay_key = st.secrets["PIXABAY_API_KEY"]

if not active_groq_key:
    st.error("🔑 GROQ_API_KEY missing! Streamlit Secrets mein add karo.")
if not active_pixabay_key:
    st.error("🔑 PIXABAY_API_KEY missing! Streamlit Secrets mein add karo.")

keys_ready = bool(active_groq_key and active_pixabay_key)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Subtitle & VFX Controls")

    sub_size = st.select_slider(
        "Subtitle Size",
        options=["Small", "Medium", "Large", "Extra Large"],
        value="Medium"
    )

    sub_style = st.selectbox(
        "Subtitle Visual Style",
        ["Kinetic Yellow", "Cyberpunk Neon", "Clean Classic", "Boxed Background"]
    )

    sub_position = st.selectbox(
        "Subtitle Position",
        ["Bottom", "Center", "Top"],
        index=0
    )

    font_choice = st.selectbox(
        "Font Style",
        ["DejaVuSans-Bold.ttf", "arial.ttf", "DejaVuSans.ttf"],
        index=0
    )

    enable_letterbox = st.checkbox("Enable Cinematic Letterbox (2.35:1)", value=True)

subtitle_config = {
    "size": sub_size,
    "style": sub_style,
    "position": sub_position,
    "font": font_choice,
    "enable_letterbox": enable_letterbox
}

# --- MAIN INTERFACE ---
user_script = st.text_area(
    "Enter Video Script / Topic:",
    value="""Futuristic neon cities are expanding across the entire world today.
Advanced high speed trains connect distant megacities in minutes.
Clean renewable solar farms generate limitless energy for humanity.
Artificial intelligence drives the next great industrial revolution forward.""",
    height=150
)

duration_option = st.selectbox(
    "Select Video Target Duration:",
    ["30 Seconds (4 Scenes)", "60 Seconds (8 Scenes)"]
)

if st.button("🚀 Render Custom HD Video", type="primary", disabled=not keys_ready):
    if not user_script.strip():
        st.warning("⚠️ Please enter a script first.")
    else:
        scene_count = 4 if "30" in duration_option else 8
        word_length = "8 to 12 words" if scene_count == 4 else "12 to 18 words"

        # Runtime pe keys set karo taaki modules use kar sakein
        os.environ["PIXABAY_API_KEY"] = active_pixabay_key

        with st.spinner("⏳ Analyzing script & rendering video... (~2-3 minutes)"):
            scenes = analyze_script(user_script, active_groq_key, scene_count, word_length)

            if not scenes:
                st.error("❌ AI Director failed to generate scenes. Check your Groq API key.")
            else:
                out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
                success = build_master_video(scenes, subtitle_config, output_filename="final_video.mp4")

                if success and os.path.exists(out_path):
                    st.success("🎉 Video rendered successfully!")
                    st.video(out_path)
                else:
                    st.error("❌ Video rendering failed. Check logs for details.")