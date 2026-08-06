import os
import shutil
import asyncio
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx
)
from modules.tts_engine import generate_voiceover
from modules.stock_fetcher import get_stock_clip
from modules.subtitle_vfx import apply_cinematic_vfx
from config import DEFAULT_PRESET, DEFAULT_BITRATE, OUTPUT_DIR, TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT

def build_master_video(scenes, bgm_path=None, output_filename="final_4sec_video.mp4"):
    """Builds a 4-second video and automatically cleans up temporary files when finished."""
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_video_clips = []
    audio_clips_list = []

    TARGET_DURATION = 4.0  # Strict 4-second video target

    for idx, scene in enumerate(scenes, start=1):
        narration = scene.get("narration", "")
        query = scene.get("search_query", "city")
        
        print(f"\n🎬 4-Second Scene: \"{narration}\"")
        
        # 1. Generate Voiceover
        audio_file = os.path.join(TEMP_DIR, f"audio_{idx:02d}.mp3")
        asyncio.run(generate_voiceover(narration, audio_file))
        audio_clip = AudioFileClip(audio_file)
        
        # Trim audio if it exceeds 4 seconds
        if audio_clip.duration > TARGET_DURATION:
            audio_clip = audio_clip.subclipped(0, TARGET_DURATION)
        
        audio_dur = min(audio_clip.duration, TARGET_DURATION)
        audio_clips_list.append(audio_clip)

        # 2. Download Stock Footage
        video_file = get_stock_clip(query, idx)
        if not video_file or not os.path.exists(video_file):
            print(f"⚠️ Video download failed for '{query}'.")
            continue

        # 3. Force Video Clip to 4.0 Seconds
        clip = VideoFileClip(video_file).resized(new_size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        if clip.duration < TARGET_DURATION:
            clip = vfx.Loop(duration=TARGET_DURATION).apply(clip)
        else:
            clip = clip.subclipped(0, TARGET_DURATION)

        # 4. Apply Subtitles & VFX over 4 seconds
        clip = clip.transform(
            lambda get_frame, t, dur=TARGET_DURATION, txt=narration: apply_cinematic_vfx(get_frame(t), txt, t, dur)
        )

        processed_video_clips.append(clip)

    if not processed_video_clips or not audio_clips_list:
        print("❌ No valid scenes processed.")
        return

    # 5. Build Final Video & Audio
    final_video = concatenate_videoclips(processed_video_clips, method="compose")
    master_voiceover = CompositeAudioClip(audio_clips_list)

    if bgm_path and os.path.exists(bgm_path):
        bgm_clip = AudioFileClip(bgm_path).subclipped(0, TARGET_DURATION)
        bgm_ducked = bgm_clip.with_volume_scaling(0.12)
        master_audio = CompositeAudioClip([master_voiceover, bgm_ducked])
    else:
        master_audio = master_voiceover

    final_video = final_video.with_audio(master_audio)

    print(f"\n🎥 Final Video Duration: {final_video.duration:.1f} seconds")
    print(f"⚡ Exporting to: {final_output_path}...")
    
    temp_audio_path = os.path.join(TEMP_DIR, "temp-audio.m4a")
    final_video.write_videofile(
        final_output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset=DEFAULT_PRESET,
        bitrate=DEFAULT_BITRATE,
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"],
        temp_audiofile=temp_audio_path,
        remove_temp=True
    )

    # 6. Close File Handles
    for c in processed_video_clips:
        c.close()
    for a in audio_clips_list:
        a.close()
    master_audio.close()
    final_video.close()

    # 7. AUTOMATIC TEMP CLEANUP: Delete temporary audio and video files
    print("\n🧹 Cleaning up all temporary clips from output/temp/...")
    if os.path.exists(TEMP_DIR):
        for item in os.listdir(TEMP_DIR):
            item_path = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
            except Exception as e:
                print(f"⚠️ Could not delete {item_path}: {e}")
    print("✅ Temp files successfully removed!")

    print(f"\n🎉 Done! Final 4-second video saved at: {final_output_path}")