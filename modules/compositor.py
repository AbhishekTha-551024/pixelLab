import os
import asyncio
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx
)
from modules.tts_engine import generate_voiceover
from modules.stock_fetcher import get_stock_clip
from modules.subtitle_vfx import apply_cinematic_vfx
from config import OUTPUT_DIR, TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, DEFAULT_PRESET, DEFAULT_BITRATE, FPS

def build_master_video(scenes, sub_config, output_filename="final_video.mp4"):
    """
    Assembles audio, downloaded HD video clips, and VFX subtitles into a crystal-clear rendered video.
    """
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_clips = []
    audio_clips_list = []

    for idx, scene in enumerate(scenes, start=1):
        narration = scene.get("narration", "")
        query = scene.get("search_query", "nature")
        
        print(f"\n🎬 Processing Scene {idx}: \"{narration}\"")
        
        # 1. Generate Voiceover Audio
        audio_file = os.path.join(TEMP_DIR, f"audio_{idx:02d}.mp3")
        asyncio.run(generate_voiceover(narration, audio_file))
        
        if not os.path.exists(audio_file):
            print(f"⚠️ Audio generation failed for scene {idx}")
            continue

        audio_clip = AudioFileClip(audio_file)
        audio_dur = audio_clip.duration
        audio_clips_list.append(audio_clip)

        # 2. Download Stock Footage (Pulls highest available 1080p/4K source)
        video_file = get_stock_clip(query, idx)
        if not video_file or not os.path.exists(video_file):
            print(f"⚠️ Stock footage download failed for query '{query}'. Skipping scene.")
            continue

        # 3. Clean Full HD 1080p Center-Crop & Resize (Prevents stretching & preserves sharpness)
        clip = VideoFileClip(video_file)
        w, h = clip.size
        target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            clip = clip.cropped(x1=(w - new_w) // 2, width=new_w)
        elif current_ratio < target_ratio:
            new_h = int(w / target_ratio)
            clip = clip.cropped(y1=(h - new_h) // 2, height=new_h)
            
        clip = clip.resized(new_size=(VIDEO_WIDTH, VIDEO_HEIGHT))

        # Loop or trim clip duration to match audio exactly
        if clip.duration < audio_dur:
            clip = vfx.Loop(duration=audio_dur).apply(clip)
        else:
            clip = clip.subclipped(0, audio_dur)

        # 4. Apply Subtitles & VFX Frame-by-Frame in High Definition
        clip = clip.transform(
            lambda get_frame, t, dur=audio_dur, txt=narration, cfg=sub_config: apply_cinematic_vfx(get_frame(t), txt, t, dur, cfg)
        )

        # 5. Attach Audio Track
        clip = clip.with_audio(audio_clip)
        processed_clips.append(clip)

    if not processed_clips:
        print("❌ No valid clips were successfully processed.")
        return False

    # 6. Concatenate & Export Master Video with High-Quality FFmpeg Flags
    print("\n⚡ Concatenating clips and rendering Full HD master video...")
    final_clip = concatenate_videoclips(processed_clips, method="compose")
    
    final_clip.write_videofile(
        final_output_path,
        codec="libx264",
        audio_codec="aac",
        fps=FPS,
        preset=DEFAULT_PRESET,
        bitrate=DEFAULT_BITRATE,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"]
    )

    # Clean up file handles
    for c in processed_clips:
        c.close()
    for a in audio_clips_list:
        a.close()
    final_clip.close()

    print(f"\n🎉 Success! High-quality video saved at: {final_output_path}")
    return True