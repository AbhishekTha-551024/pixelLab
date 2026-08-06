import os
import json
import asyncio
import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from groq import Groq
import streamlit as st
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx
)

# --- CONFIGURATION & DIRECTORY SETUP ---
OUTPUT_DIR = "output"
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

VOICE = "en-US-ChristopherNeural"
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "57035971-d6e26400d6d412197a79cbba8")

GROQ_API_KEY = ""
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- TTS GENERATION ---
async def generate_voiceover(text, output_file):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

# --- DYNAMIC SUBTITLE ENGINE WITH CUSTOM OPTIONS ---
def draw_kinetic_subtitles(frame, text, t, duration, sub_config):
    """Renders highly-customizable kinetic subtitles based on user settings."""
    if not text or not text.strip():
        return frame

    h, w = frame.shape[:2]
    words = text.split()
    if not words:
        return frame

    progress = max(0, min(1, t / max(duration, 0.1)))
    active_idx = int(progress * len(words))
    active_idx = min(active_idx, len(words) - 1)

    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    # 1. Font Size Calculation
    size_map = {
        "Small": 0.038,
        "Medium": 0.055,
        "Large": 0.072,
        "Extra Large": 0.090
    }
    font_size = max(20, int(h * size_map.get(sub_config["size"], 0.055)))

    # 2. Font File Selection
    font_file = sub_config["font"]
    font = None
    try:
        font = ImageFont.truetype(font_file, font_size)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.load_default(size=font_size)
            except TypeError:
                font = ImageFont.load_default()

    # 3. Y-Position Calculation
    pos_map = {
        "Bottom": 0.80,
        "Center": 0.45,
        "Top": 0.15
    }
    start_y = int(h * pos_map.get(sub_config["position"], 0.80))

    # Calculate total dimensions
    total_text = " ".join(words)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    start_x = max(20, (w - text_w) // 2)

    # 4. Optional Semi-Transparent Box Background
    if sub_config["style"] == "Boxed Background":
        padding_x = 20
        padding_y = 12
        box_rect = [
            max(10, start_x - padding_x),
            start_y - padding_y,
            min(w - 10, start_x + text_w + padding_x),
            start_y + text_h + padding_y
        ]
        draw.rectangle(box_rect, fill=(0, 0, 0, 160))

    # 5. Word-by-Word Rendering
    current_x = start_x
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    for idx, word in enumerate(words):
        word_w = draw.textbbox((0, 0), word, font=font)[2]

        # Style Color Profiles
        if sub_config["style"] == "Kinetic Yellow":
            color = (255, 235, 59) if idx == active_idx else (255, 255, 255)
            stroke_color = (0, 0, 0)
        elif sub_config["style"] == "Cyberpunk Neon":
            color = (0, 255, 255) if idx == active_idx else (255, 255, 255)
            stroke_color = (255, 0, 128) if idx == active_idx else (0, 0, 0)
        elif sub_config["style"] == "Clean Classic":
            color = (255, 255, 255)
            stroke_color = (0, 0, 0)
        else:  # Boxed Background
            color = (255, 235, 59) if idx == active_idx else (255, 255, 255)
            stroke_color = (0, 0, 0)

        # Thick Outline Stroke for Legibility
        stroke_radius = max(2, int(font_size * 0.08))
        for stroke_x in range(-stroke_radius, stroke_radius + 1):
            for stroke_y in range(-stroke_radius, stroke_radius + 1):
                draw.text((current_x + stroke_x, start_y + stroke_y), word, font=font, fill=stroke_color)

        draw.text((current_x, start_y), word, font=font, fill=color)
        current_x += word_w + space_w

    return np.array(img.convert("RGB"))

def apply_cinematic_vfx(frame, text, t, duration, sub_config):
    """VFX Pipeline: Contrast boost + Optional Letterbox + Subtitles."""
    h, w = frame.shape[:2]

    # Contrast & Saturation Boost
    frame = cv2.convertScaleAbs(frame, alpha=1.05, beta=2)

    # 2.35:1 Letterbox Bar Option
    if sub_config.get("enable_letterbox", True):
        bar_height = int((h - (w / 2.35)) / 2)
        if bar_height > 0:
            frame[:bar_height, :] = 0
            frame[h - bar_height:, :] = 0

    return draw_kinetic_subtitles(frame, text, t, duration, sub_config)

# --- AI DIRECTOR ---
def analyze_script(script_text, scene_count, word_length):
    if not client:
        return []

    system_instruction = (
        f"You are a film director. Break the script into EXACTLY {scene_count} distinct scenes. "
        f"Each scene narration should be {word_length} long. "
        "For each scene, return: "
        "1. 'narration': Clear narration sentence. "
        "2. 'search_query': Simple stock footage search query (1-2 words). "
        f"Return ONLY a JSON object with a 'scenes' array containing {scene_count} scene objects."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Script:\n{script_text}"}
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    
    try:
        parsed = json.loads(chat_completion.choices[0].message.content)
        return parsed.get("scenes", [])
    except Exception as e:
        print(f"⚠️ Prompt parsing error: {e}")
        return []

# --- HIGH QUALITY STOCK FETCH ---
def get_stock_clip(search_query, index):
    """Downloads HD stock footage from Pixabay."""
    filename = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_query}&min_width=1920&per_page=5"
    
    try:
        res = requests.get(url).json()
        hits = res.get("hits", [])
        if not hits:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q=landscape&min_width=1280&per_page=5"
            res = requests.get(url).json()
            hits = res.get("hits", [])

        if hits:
            v_info = hits[0].get("videos", {})
            d_url = (
                v_info.get("large", {}).get("url")
                or v_info.get("medium", {}).get("url")
                or v_info.get("small", {}).get("url")
            )
            if d_url:
                with open(filename, "wb") as f:
                    f.write(requests.get(d_url).content)
                return filename
    except Exception as e:
        print(f"❌ Error fetching stock clip for '{search_query}': {e}")
    return None

# --- COMPOSITOR ENGINE ---
def build_master_video(scenes, sub_config, output_filename="final_video.mp4"):
    processed_clips = []
    audio_clips_list = []

    for idx, scene in enumerate(scenes, start=1):
        narration = scene.get("narration", "")
        query = scene.get("search_query", "nature")
        
        # 1. Voiceover
        audio_file = os.path.join(TEMP_DIR, f"audio_{idx:02d}.mp3")
        asyncio.run(generate_voiceover(narration, audio_file))
        audio_clip = AudioFileClip(audio_file)
        audio_dur = audio_clip.duration
        audio_clips_list.append(audio_clip)

        # 2. Stock Footage
        video_file = get_stock_clip(query, idx)
        if not video_file or not os.path.exists(video_file):
            continue

        # 3. Clean 1080p Crop
        clip = VideoFileClip(video_file)
        w, h = clip.size
        target_ratio = 16 / 9
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            clip = clip.cropped(x1=(w - new_w) // 2, width=new_w)
        elif current_ratio < target_ratio:
            new_h = int(w / target_ratio)
            clip = clip.cropped(y1=(h - new_h) // 2, height=new_h)
            
        clip = clip.resized(new_size=(1920, 1080))

        if clip.duration < audio_dur:
            clip = vfx.Loop(duration=audio_dur).apply(clip)
        else:
            clip = clip.subclipped(0, audio_dur)

        # 4. Render Frame-by-Frame with User Subtitle Options
        clip = clip.transform(
            lambda get_frame, t, dur=audio_dur, txt=narration, cfg=sub_config: apply_cinematic_vfx(get_frame(t), txt, t, dur, cfg)
        )

        clip = clip.with_audio(audio_clip)
        processed_clips.append(clip)

    if not processed_clips:
        return False

    # 5. Export Master Video
    final_clip = concatenate_videoclips(processed_clips, method="compose")
    
    final_clip.write_videofile(
        output_filename,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        bitrate="12000k",
        ffmpeg_params=["-crf", "18"]
    )

    for c in processed_clips:
        c.close()
    for a in audio_clips_list:
        a.close()

    return True

# --- STREAMLIT UI WITH FULL CONTROLS ---
st.set_page_config(page_title="Pixelab - AI Video Generator", page_icon="🎬", layout="wide")

st.title("🎬 Pixelab - AI Video Generator")
st.caption("Generate cinematic HD videos with customizable subtitles & AI voiceover.")

if not GROQ_API_KEY:
    st.error("🔑 GROQ_API_KEY is missing! Add it in Streamlit Secrets.")

# --- SIDEBAR CONTROLS ---
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

# Package Subtitle Settings
subtitle_config = {
    "size": sub_size,
    "style": sub_style,
    "position": sub_position,
    "font": font_choice,
    "enable_letterbox": enable_letterbox
}

# --- MAIN CONTENT ---
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

if st.button("🚀 Render Custom HD Video", type="primary", disabled=not GROQ_API_KEY):
    if not user_script.strip():
        st.warning("⚠️ Please enter a script first.")
    else:
        scene_count = 4 if "30" in duration_option else 8
        word_length = "8 to 12 words" if scene_count == 4 else "12 to 18 words"

        with st.spinner("⏳ Rendering video with your custom subtitle choices... (~1 min)"):
            scenes = analyze_script(user_script, scene_count, word_length)
            
            if not scenes:
                st.error("❌ AI Director failed to generate scenes. Check your Groq API key.")
            else:
                out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
                success = build_master_video(scenes, subtitle_config, output_filename=out_path)
                
                if success and os.path.exists(out_path):
                    st.success("🎉 Video rendered successfully with your selected subtitle settings!")
                    st.video(out_path)
                else:
                    st.error("❌ Video rendering failed.")