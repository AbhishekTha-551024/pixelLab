from modules.ai_director import analyze_script
from modules.compositor import build_master_video

def main():
    script_text = """
    Futuristic neon cities are expanding across the entire world today.
    Advanced high speed trains connect distant megacities in minutes.
    Clean renewable solar farms generate limitless energy for humanity.
    Artificial intelligence drives the next great industrial revolution forward.
    """

    scenes = analyze_script(script_text)
    print(f"✨ Created {len(scenes)} scenes.")
    
    if scenes:
        build_master_video(scenes, "final_video.mp4")

if __name__ == "__main__":
    main()