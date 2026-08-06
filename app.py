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

# --- SUBTITLES & VFX (HD ENHANCED) ---
def draw_kinetic_subtitles(frame, text, t, duration):
    """Renders prominent, highly-legible kinetic subtitles across platforms."""
    if not text:
        return frame

    h, w = frame.shape[:2]
    words = text.split()
    if not words:
        return frame

    progress = max(0, min(1, t / max(duration, 0.1)))
    active_idx = int(progress * len(words))
    active_idx = min(active_idx, len(words) - 1)

    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    # Dynamic high-resolution font sizing (6% of frame height)
    font_size = max(28, int(h * 0.055))
    
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # High-res default fallback for Linux cloud environments
            try:
                font = ImageFont.load_default(size=font_size)
            except TypeError:
                font = ImageFont.load_default()

    total_text = " ".join(words)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    text_w = bbox[2] - bbox[0]
    
    start_x = max(20, (w - text_w) // 2)
    start_y = int(h * 0.80)

    current_x = start_x
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    for idx, word in enumerate(words):
        word_w = draw.textbbox((0, 0), word, font=font)[2]
        color = (255, 235, 59) if idx == active_idx else (255, 255, 255)
        
        # Thick black outline stroke for maximum readability on any background
        stroke_radius = max(2, int(font_size * 0.08))
        for stroke_x in range(-stroke_radius, stroke_radius + 1):
            for stroke_y in range(-stroke_radius, stroke_radius + 1):
                draw.text((current_x + stroke_x, start_y + stroke_y), word, font=font, fill=(0, 0, 0))
        
        draw.text((current_x, start_y), word, font=font, fill=color)
        current_x += word_w + space_w

    return np.array(img)

def apply_cinematic_vfx(frame, text, t, duration):
    """Visual pipeline: Contrast adjustment + Letterbox + Subtitles."""
    h, w = frame.shape[:2]

    # Subtle contrast and saturation boost
    frame = cv2.convertScaleAbs(frame, alpha=1.05, beta=2)

    # Cinematic 2.35:1 Letterbox bars
    bar_height = int((h - (w / 2.35)) / 2)
    if bar_height > 0:
        frame[:bar_height, :] = 0
        frame[h - bar_height:, :] = 0

    return draw_kinetic_subtitles(frame, text, t, duration)

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
    """Downloads HD (1080p/720p) stock footage from Pixabay."""
    filename = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_query}&min_width=1920&per_page=5"
    
    try:
        res = requests.get(url).json()
        hits = res.get("hits", [])
        if not hits:
            # Fallback query if specific search yields no HD hits
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q=landscape&min_width=1280&per_page=5"
            res = requests.get(url).json()
            hits = res.get("hits", [])

        if hits:
            v_info = hits[0].get("videos", {})
            # Prioritize Large (1080p) -> Medium (720p)
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

# --- COMPOSITOR ENGINE (HIGH BITRATE EXPORT) ---
def build_master_video(scenes, output_filename="final_video.mp4"):
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

        # 3. Clip Processing without aspect stretching
        clip = VideoFileClip(video_file)
        
        # Center-crop/resize to 1920x1080 cleanly
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

        # Loop or crop duration to match audio
        if clip.duration < audio_dur:
            clip = vfx.Loop(duration=audio_dur).apply(clip)
        else:
            clip = clip.subclipped(0, audio_dur)

        # 4. Apply Subtitles & VFX
        clip = clip.transform(
            lambda get_frame, t, dur=audio_dur, txt=narration: apply_cinematic_vfx(get_frame(t), txt, t, dur)
        )

        # 5. Attach Audio
        clip = clip.with_audio(audio_clip)
        processed_clips.append(clip)

    if not processed_clips:
        return False

    # 6. High Quality Render (12 Mbps, CRF 18)
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

# --- STREAMLIT UI ---
st.set_page_config(page_title="Pixelab - AI Video Generator", page_icon="🎬")

st.title("🎬 Pixelab - AI Video Generator")
st.caption("Generate cinematic HD videos with AI voiceover and kinetic subtitles.")

if not GROQ_API_KEY:
    st.error("🔑 GROQ_API_KEY is missing! Add it in Streamlit Secrets.")

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

if st.button("🚀 Render HD Video", type="primary", disabled=not GROQ_API_KEY):
    if not user_script.strip():
        st.warning("⚠️ Please enter a script first.")
    else:
        scene_count = 4 if "30" in duration_option else 8
        word_length = "8 to 12 words" if scene_count == 4 else "12 to 18 words"

        with st.spinner(f"⏳ Processing HD scenes & rendering video... (~1 min)"):
            scenes = analyze_script(user_script, scene_count, word_length)
            
            if not scenes:
                st.error("❌ AI Director failed to generate scenes. Check your Groq API key.")
            else:
                out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
                success = build_master_video(scenes, output_filename=out_path)
                
                if success and os.path.exists(out_path):
                    st.success("🎉 HD Video rendered successfully!")
                    st.video(out_path)
                else:
                    st.error("❌ Video rendering failed.")