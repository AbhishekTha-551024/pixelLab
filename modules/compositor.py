import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, vfx
from modules.tts_engine import generate_voiceover
from modules.stock_fetcher import get_stock_clip
from modules.subtitle_vfx import apply_cinematic_vfx
from config import OUTPUT_DIR, TEMP_DIR, DEFAULT_PRESET, DEFAULT_BITRATE

# Resolution presets
RESOLUTION_MAP = {
    "1920×1080 (Full HD)":       (1920, 1080),
    "1280×720 (HD)":             (1280, 720),
    "1080×1920 (Portrait FHD)":  (1080, 1920),
    "1080×1080 (Square)":        (1080, 1080),
}

def apply_subtitles_with_time(clip, narration, duration, config):
    def subtitle_filter(get_frame, t):
        return apply_cinematic_vfx(get_frame(t), narration, t, duration, config)
    return clip.transform(subtitle_filter)


def build_master_video(scenes, config, output_filename="final_video.mp4"):
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_clips   = []
    audio_clips_list  = []

    res_key    = config.get("resolution", "1920×1080 (Full HD)")
    VIDEO_W, VIDEO_H = RESOLUTION_MAP.get(res_key, (1920, 1080))
    FPS        = config.get("fps", 24)
    voice      = config.get("voice", "en-US-ChristopherNeural")
    speed      = config.get("voice_speed", "Normal")
    fade_dur   = config.get("fade_duration", 0) if config.get("enable_fade") else 0

    for idx, scene in enumerate(scenes, start=1):
        narration = scene.get("narration", "")
        query     = scene.get("search_query", "nature")
        print(f"\n🎬 Scene {idx}: \"{narration}\"")

        # 1. TTS
        audio_file = os.path.join(TEMP_DIR, f"audio_{idx:02d}.mp3")
        generate_voiceover(narration, audio_file, voice=voice, speed=speed)

        if not os.path.exists(audio_file):
            print(f"⚠️ Audio failed scene {idx}, skipping.")
            continue

        audio_clip = AudioFileClip(audio_file)
        audio_dur  = audio_clip.duration
        audio_clips_list.append(audio_clip)

        # 2. Stock footage
        video_file = get_stock_clip(query, idx)
        if not video_file or not os.path.exists(video_file):
            print(f"⚠️ Stock failed '{query}', skipping.")
            audio_clip.close()
            continue

        # 3. Crop & resize
        clip = VideoFileClip(video_file)
        w, h = clip.size
        target_ratio  = VIDEO_W / VIDEO_H
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            clip  = clip.cropped(x1=(w - new_w) // 2, width=new_w)
        elif current_ratio < target_ratio:
            new_h = int(w / target_ratio)
            clip  = clip.cropped(y1=(h - new_h) // 2, height=new_h)

        clip = clip.resized(new_size=(VIDEO_W, VIDEO_H))

        # 4. Loop/trim
        if clip.duration < audio_dur:
            clip = clip.with_effects([vfx.Loop(duration=audio_dur)])
        else:
            clip = clip.subclipped(0, audio_dur)

        # 5. Ken Burns zoom
        if config.get("enable_zoom"):
            direction = config.get("zoom_direction", "Slow Zoom In")
            def zoom_filter(get_frame, t, dur=audio_dur, d=direction):
                frame = get_frame(t)
                progress = t / max(dur, 0.1)
                if d == "Slow Zoom In":
                    scale = 1.0 + 0.04 * progress
                elif d == "Slow Zoom Out":
                    scale = 1.04 - 0.04 * progress
                else:
                    import random
                    scale = 1.0 + 0.04 * (progress if random.random() > 0.5 else (1 - progress))
                import cv2
                fh, fw = frame.shape[:2]
                new_w2 = int(fw * scale)
                new_h2 = int(fh * scale)
                resized = cv2.resize(frame, (new_w2, new_h2))
                x1 = (new_w2 - fw) // 2
                y1 = (new_h2 - fh) // 2
                return resized[y1:y1+fh, x1:x1+fw]
            clip = clip.transform(zoom_filter)

        # 6. Subtitles + VFX
        clip = apply_subtitles_with_time(clip, narration, audio_dur, config)

        # 7. Fade transition
        if fade_dur > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(fade_dur), vfx.CrossFadeOut(fade_dur)])

        clip = clip.with_audio(audio_clip)
        processed_clips.append(clip)

    if not processed_clips:
        print("❌ No clips processed.")
        return False

    print("\n⚡ Rendering final video...")
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

    for c in processed_clips:
        try: c.close()
        except: pass
    for a in audio_clips_list:
        try: a.close()
        except: pass
    final_clip.close()

    # Cleanup
    if os.path.exists(TEMP_DIR):
        for item in os.listdir(TEMP_DIR):
            p = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(p): os.remove(p)
            except: pass

    print(f"\n🎉 Done: {final_output_path}")
    return True