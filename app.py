import os
import streamlit as st
from config import GROQ_API_KEY, OUTPUT_DIR
from modules.ai_director import analyze_script
from modules.compositor import build_master_video

# --- STREAMLIT PAGE SETUP ---
st.set_page_config(
    page_title="Pixelab - AI Video Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Pixelab - AI Video Generator")
st.caption("Generate cinematic HD short videos with custom subtitles and AI voiceover.")

# Check for API key availability
active_api_key = GROQ_API_KEY
if "GROQ_API_KEY" in st.secrets:
    active_api_key = st.secrets["GROQ_API_KEY"]

if not active_api_key:
    st.error("🔑 GROQ_API_KEY is missing! Please configure it in your Streamlit Secrets.")

# --- SIDEBAR: ADVANCED SUBTITLE & VFX CONTROLS ---
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
    value="""Robot helpers assist humans daily in modern smart homes.
Precision robots save lives during complex medical surgeries.
Robots harvest many crops efficiently across modern farms.
Robots build tall skyscrapers swiftly using advanced automation.""",
    height=150
)

duration_option = st.selectbox(
    "Select Video Target Duration:",
    ["30 Seconds (4 Scenes)", "60 Seconds (8 Scenes)"]
)

if st.button("🚀 Render Custom HD Video", type="primary", disabled=not active_api_key):
    if not user_script.strip():
        st.warning("⚠️ Please enter a script first.")
    else:
      scene_count = 4 if "30" in duration_option else 8
      word_length = "8 to 12 words" if scene_count == 4 else "12 to 18 words"

      with st.spinner("⏳ Analyzing script with AI Director & rendering video... (~1 minute)"):
        scenes = analyze_script(active_api_key, user_script, scene_count, word_length)
        
        if not scenes:
          st.error("❌ AI Director failed to generate scenes. Check your Groq API key.")
        else:
          out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
          success = build_master_video(scenes, subtitle_config, output_filename="final_video.mp4")
          
          if success and os.path.exists(out_path):
            st.success("🎉 Video rendered successfully with your selected custom settings!")
            st.video(out_path)
          else:
            st.error("❌ Video rendering failed during compilation.")