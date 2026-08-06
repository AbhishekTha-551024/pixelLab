import os
import streamlit as st
from config import GROQ_API_KEY, PIXABAY_API_KEY, OUTPUT_DIR
from modules.ai_director import analyze_script
from modules.compositor import build_master_video

st.set_page_config(
    page_title="Pixelab - AI Video Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Pixelab - AI Video Generator")
st.caption("Generate cinematic HD short videos with full professional controls.")

# --- API KEYS ---
active_groq_key = GROQ_API_KEY
active_pixabay_key = PIXABAY_API_KEY
if "GROQ_API_KEY" in st.secrets:
    active_groq_key = st.secrets["GROQ_API_KEY"]
if "PIXABAY_API_KEY" in st.secrets:
    active_pixabay_key = st.secrets["PIXABAY_API_KEY"]

if not active_groq_key:
    st.error("🔑 GROQ_API_KEY missing!")
if not active_pixabay_key:
    st.error("🔑 PIXABAY_API_KEY missing!")

keys_ready = bool(active_groq_key and active_pixabay_key)

# ============================================================
# SIDEBAR — ALL CONTROLS
# ============================================================
with st.sidebar:

    # ── 1. VIDEO LAYOUT ──────────────────────────────────────
    st.header("📐 Video Layout")

    aspect_ratio = st.selectbox(
        "Aspect Ratio",
        ["16:9 Landscape (YouTube)", "9:16 Portrait (Reels/Shorts)", "1:1 Square (Instagram)", "4:3 Classic", "2.35:1 Cinematic Ultrawide"],
        index=0
    )

    resolution = st.selectbox(
        "Resolution",
        ["1920×1080 (Full HD)", "1280×720 (HD)", "1080×1920 (Portrait FHD)", "1080×1080 (Square)"],
        index=0
    )

    fps_choice = st.select_slider(
        "Frame Rate (FPS)",
        options=[24, 30, 60],
        value=24
    )

    video_duration = st.selectbox(
        "Video Duration",
        ["15 Seconds (2 Scenes)", "30 Seconds (4 Scenes)", "45 Seconds (6 Scenes)", "60 Seconds (8 Scenes)"],
        index=1
    )

    st.divider()

    # ── 2. COLOR GRADING ─────────────────────────────────────
    st.header("🎨 Color Grading")

    color_grade = st.selectbox(
        "Color Grade Preset",
        ["None", "Cinematic Teal & Orange", "Warm Sunset", "Cold Blue Steel", "Vintage Film", "High Contrast B&W", "Moody Dark", "Vibrant Pop", "Golden Hour"],
        index=0
    )

    brightness = st.slider("Brightness", min_value=-50, max_value=50, value=2, step=1)
    contrast = st.slider("Contrast", min_value=0.5, max_value=2.0, value=1.05, step=0.05)
    saturation = st.slider("Saturation", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
    vignette_strength = st.slider("Vignette Strength", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

    st.divider()

    # ── 3. SUBTITLE STYLE ────────────────────────────────────
    st.header("💬 Subtitle Style")

    sub_style = st.selectbox(
        "Subtitle Visual Style",
        ["Kinetic Yellow", "Cyberpunk Neon", "Clean Classic", "Boxed Background",
         "Fire Red", "Instagram White", "MrBeast Bold", "Gradient Rainbow", "Minimal Fade"],
        index=0
    )

    sub_size = st.select_slider(
        "Subtitle Size",
        options=["Tiny", "Small", "Medium", "Large", "Extra Large", "Massive"],
        value="Medium"
    )

    sub_position = st.selectbox(
        "Subtitle Position",
        ["Bottom", "Lower Center", "Center", "Upper Center", "Top"],
        index=0
    )

    sub_animation = st.selectbox(
        "Word Highlight Animation",
        ["Active Word Highlight", "Karaoke Underline", "Scale Pop", "All White (No Animation)", "Fade In Words"],
        index=0
    )

    sub_alignment = st.selectbox(
        "Text Alignment",
        ["Center", "Left", "Right"],
        index=0
    )

    font_choice = st.selectbox(
        "Font",
        ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "DejaVuSerif-Bold.ttf", "DejaVuSerif.ttf", "DejaVuSansMono-Bold.ttf"],
        index=0
    )

    stroke_width = st.slider("Text Stroke / Outline Width", min_value=0, max_value=10, value=3, step=1)

    st.divider()

    # ── 4. CINEMATIC VFX ─────────────────────────────────────
    st.header("🎬 Cinematic VFX")

    enable_letterbox = st.checkbox("Cinematic Letterbox Bars", value=True)

    letterbox_ratio = st.selectbox(
        "Letterbox Ratio",
        ["2.35:1 (Anamorphic)", "2.39:1 (Ultra Scope)", "1.85:1 (Flat)"],
        index=0,
        disabled=not enable_letterbox
    )

    enable_zoom = st.checkbox("Ken Burns Zoom Effect", value=False)
    zoom_direction = st.selectbox(
        "Zoom Direction",
        ["Slow Zoom In", "Slow Zoom Out", "Random per Scene"],
        disabled=not enable_zoom
    )

    enable_fade = st.checkbox("Scene Fade Transitions", value=True)
    fade_duration = st.slider("Fade Duration (seconds)", 0.1, 1.0, 0.3, 0.1, disabled=not enable_fade)

    enable_grain = st.checkbox("Film Grain Effect", value=False)
    grain_intensity = st.slider("Grain Intensity", 0.0, 1.0, 0.3, 0.1, disabled=not enable_grain)

    st.divider()

    # ── 5. VOICE / AUDIO ─────────────────────────────────────
    st.header("🎙️ Voice & Audio")

    voice_choice = st.selectbox(
        "AI Voice",
        [
            "en-US-ChristopherNeural (Male, Deep)",
            "en-US-JennyNeural (Female, Warm)",
            "en-US-GuyNeural (Male, News)",
            "en-US-AriaNeural (Female, Expressive)",
            "en-GB-RyanNeural (British Male)",
            "en-GB-SoniaNeural (British Female)",
            "en-AU-NatashaNeural (Australian Female)",
            "en-IN-NeerjaNeural (Indian Female)",
        ],
        index=0
    )

    voice_speed = st.select_slider(
        "Voice Speed",
        options=["Extra Slow", "Slow", "Normal", "Fast", "Extra Fast"],
        value="Normal"
    )

    enable_bg_music = st.checkbox("Background Music (coming soon)", value=False, disabled=True)

    st.divider()

    # ── 6. AI DIRECTOR ───────────────────────────────────────
    st.header("🤖 AI Director Settings")

    ai_tone = st.selectbox(
        "Script Tone",
        ["Cinematic & Epic", "Documentary", "Motivational", "News Style", "Story Narrative", "Educational", "Dramatic"],
        index=0
    )

    ai_language = st.selectbox(
        "Script Language",
        ["English", "Hindi", "Hinglish", "Spanish", "French", "German", "Arabic"],
        index=0
    )

# ============================================================
# PACK ALL CONFIG
# ============================================================
video_config = {
    # Layout
    "aspect_ratio": aspect_ratio,
    "resolution": resolution,
    "fps": fps_choice,
    # Color
    "color_grade": color_grade,
    "brightness": brightness,
    "contrast": contrast,
    "saturation": saturation,
    "vignette": vignette_strength,
    # Subtitles
    "style": sub_style,
    "size": sub_size,
    "position": sub_position,
    "animation": sub_animation,
    "alignment": sub_alignment,
    "font": font_choice,
    "stroke_width": stroke_width,
    # VFX
    "enable_letterbox": enable_letterbox,
    "letterbox_ratio": letterbox_ratio if enable_letterbox else None,
    "enable_zoom": enable_zoom,
    "zoom_direction": zoom_direction if enable_zoom else None,
    "enable_fade": enable_fade,
    "fade_duration": fade_duration if enable_fade else 0,
    "enable_grain": enable_grain,
    "grain_intensity": grain_intensity if enable_grain else 0,
    # Voice
    "voice": voice_choice.split(" (")[0],
    "voice_speed": voice_speed,
    # AI
    "ai_tone": ai_tone,
    "ai_language": ai_language,
}

# ============================================================
# MAIN INTERFACE
# ============================================================
col1, col2 = st.columns([3, 1])

with col1:
    user_script = st.text_area(
        "📝 Enter Video Script / Topic:",
        value="""Futuristic neon cities are expanding across the entire world today.
Advanced high speed trains connect distant megacities in minutes.
Clean renewable solar farms generate limitless energy for humanity.
Artificial intelligence drives the next great industrial revolution forward.""",
        height=160
    )

with col2:
    st.markdown("**⚙️ Quick Settings**")
    st.caption(f"📐 {aspect_ratio.split('(')[0].strip()}")
    st.caption(f"🎨 Grade: {color_grade}")
    st.caption(f"💬 Style: {sub_style}")
    st.caption(f"🎙️ Voice: {voice_choice.split(' (')[0]}")
    st.caption(f"🤖 Tone: {ai_tone}")

# Scene count from duration
duration_map = {
    "15 Seconds (2 Scenes)": (2, "6 to 10 words"),
    "30 Seconds (4 Scenes)": (4, "8 to 12 words"),
    "45 Seconds (6 Scenes)": (6, "10 to 14 words"),
    "60 Seconds (8 Scenes)": (8, "12 to 18 words"),
}
scene_count, word_length = duration_map[video_duration]

st.info(f"🎬 Will generate **{scene_count} scenes** | Tone: **{ai_tone}** | Voice: **{voice_choice.split('(')[0].strip()}** | FPS: **{fps_choice}**")

if st.button("🚀 Render Video", type="primary", disabled=not keys_ready, use_container_width=True):
    if not user_script.strip():
        st.warning("⚠️ Please enter a script first.")
    else:
        os.environ["PIXABAY_API_KEY"] = active_pixabay_key

        with st.spinner("⏳ AI Director analyzing + rendering... (~2-3 minutes)"):
            scenes = analyze_script(
                user_script, active_groq_key, scene_count, word_length,
                tone=video_config["ai_tone"],
                language=video_config["ai_language"]
            )

            if not scenes:
                st.error("❌ AI Director failed. Check your Groq API key.")
            else:
                out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
                success = build_master_video(scenes, video_config, output_filename="final_video.mp4")

                if success and os.path.exists(out_path):
                    st.success("🎉 Video rendered successfully!")
                    st.video(out_path)

                    with open(out_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Video",
                            f,
                            file_name="pixelab_video.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                else:
                    st.error("❌ Rendering failed. Check logs.")