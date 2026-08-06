import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def draw_kinetic_subtitles(frame, text, t, duration, sub_config):
    """
    Renders highly-customizable kinetic subtitles based on user settings.
    """
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
    font_size = max(20, int(h * size_map.get(sub_config.get("size", "Medium"), 0.055)))

    # 2. Font File Selection
    font_file = sub_config.get("font", "DejaVuSans-Bold.ttf")
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
    start_y = int(h * pos_map.get(sub_config.get("position", "Bottom"), 0.80))

    # Calculate total dimensions
    total_text = " ".join(words)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    start_x = max(20, (w - text_w) // 2)

    # 4. Optional Semi-Transparent Box Background Style
    if sub_config.get("style") == "Boxed Background":
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

        style = sub_config.get("style", "Kinetic Yellow")
        if style == "Kinetic Yellow":
            color = (255, 235, 59) if idx == active_idx else (255, 255, 255)
            stroke_color = (0, 0, 0)
        elif style == "Cyberpunk Neon":
            color = (0, 255, 255) if idx == active_idx else (255, 255, 255)
            stroke_color = (255, 0, 128) if idx == active_idx else (0, 0, 0)
        elif style == "Clean Classic":
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