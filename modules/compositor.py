import os
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx
)
from modules.tts_engine import generate_voiceover  # ✅ FIX #2: Ab sync function hai
from modules.stock_fetcher import get_stock_clip
from modules.subtitle_vfx import apply_cinematic_vfx
from config import OUTPUT_DIR, TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, DEFAULT_PRESET, DEFAULT_BITRATE, FPS

def build_master_video(scenes, sub_config, output_filename="final_video.mp4"):
    """
    Assembles audio, stock video clips, and VFX subtitles into final rendered video.
    """
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_clips = []
    audio_clips_list = []

    for idx, scene in enumerate(scenes, start=1):
        narration = scene.get("narration", "")
        query = scene.get("search_query", "nature")
        
        print(f"\n🎬 Processing Scene {idx}: \"{narration}\"")
        
        # 1. Generate Voiceover Audio
        # ✅ FIX #2: asyncio.run() hata diya — ab direct sync call hai
        audio_file = os.path.join(TEMP_DIR, f"audio_{idx:02d}.mp3")
        generate_voiceover(narration, audio_file)
        
        if not os.path.exists(audio_file):
            print(f"⚠️ Audio generation failed for scene {idx}")
            continue

        audio_clip = AudioFileClip(audio_file)
        audio_dur = audio_clip.duration
        audio_clips_list.append(audio_clip)

        # 2. Download Stock Footage
        video_file = get_stock_clip(query, idx)
        if not video_file or not os.path.exists(video_file):
            print(f"⚠️ Stock footage download failed for query '{query}'. Skipping scene.")
            audio_clip.close()
            continue

        # 3. Center-Crop & Resize to target resolution
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

        # ✅ FIX #4 & #5: Loop aur subclip ka sahi MoviePy v2 syntax
        if clip.duration < audio_dur:
            # MoviePy v2 mein Loop VFX ka sahi tarika
            clip = clip.with_effects([vfx.Loop(duration=audio_dur)])
        else:
            # subclipped() → subclip() — MoviePy v2 ka sahi method
            clip = clip.subclipped(0, audio_dur)

        # 4. Apply Subtitles & VFX
        # ✅ FIX #1: transform() ka MoviePy v2 sahi syntax
        # image_transform() use karo frame-level processing ke liye
        narration_text = narration
        config_copy = dict(sub_config)
        
        clip = clip.image_transform(
            lambda frame, txt=narration_text, dur=audio_dur, cfg=config_copy:
                apply_cinematic_vfx(frame, txt, 0, dur, cfg)  
                # Note: time-based word highlight ke liye neeche wala method use hoga
        )

        # Better approach: time_transform use karo kinetic subtitle ke liye
        # image_transform mein 't' nahi milta, isliye fl_time trick use karte hain
        clip = apply_subtitles_with_time(clip, narration, audio_dur, sub_config)

        # 5. Attach Audio Track
        clip = clip.with_audio(audio_clip)
        processed_clips.append(clip)

    if not processed_clips:
        print("❌ No valid clips were successfully processed.")
        return False

    # 6. Concatenate & Export
    print("\n⚡ Concatenating clips and rendering video...")
    final_clip = concatenate_videoclips(processed_clips, method="compose")
    
    temp_audio_path = os.path.join(TEMP_DIR, "temp-audio.m4a")
    final_clip.write_videofile(
        final_output_path,
        codec="libx264",
        audio_codec="aac",
        fps=FPS,
        preset=DEFAULT_PRESET,
        bitrate=DEFAULT_BITRATE,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"],
        temp_audiofile=temp_audio_path,
        remove_temp=True
    )

    # 7. Close File Handles
    for c in processed_clips:
        try:
            c.close()
        except Exception:
            pass
    for a in audio_clips_list:
        try:
            a.close()
        except Exception:
            pass
    final_clip.close()

    # 8. Cleanup temp files
    print("\n🧹 Cleaning up temporary files...")
    if os.path.exists(TEMP_DIR):
        for item in os.listdir(TEMP_DIR):
            item_path = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
            except Exception as e:
                print(f"⚠️ Could not delete {item_path}: {e}")
    print("✅ Temp files purged!")
    print(f"\n🎉 Video saved at: {final_output_path}")
    return True


def apply_subtitles_with_time(clip, narration, duration, sub_config):
    """
    ✅ FIX #1 (Final): MoviePy v2 mein time-aware frame processing ka sahi tarika.
    fl() method use karo jisme (get_frame, t) dono milte hain.
    """
    def subtitle_filter(get_frame, t):
        frame = get_frame(t)
        return apply_cinematic_vfx(frame, narration, t, duration, sub_config)
    
    return clip.fl(subtitle_filter)