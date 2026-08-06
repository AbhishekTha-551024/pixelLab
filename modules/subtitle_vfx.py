import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def draw_netflix_style_subtitles(frame, text, t, duration):
    """
    Renders BBC/Netflix documentary-style subtitles:
    - Clean Sans-Serif Typography
    - Semi-transparent dark background plate for 100% legibility
    - Active word highlight (Soft Gold/Yellow)
    - 3-5 word semantic phrase chunking
    """
    if not text:
        return frame

    h, w = frame.shape[:2]
    words = text.split()
    if not words:
        return frame

    # 1. Determine current active word based on time progress
    progress = max(0, min(1, t / max(duration, 0.1)))
    active_idx = min(int(progress * len(words)), len(words) - 1)

    # 2. Convert OpenCV BGR frame to PIL RGB Image
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img, "RGBA")

    # 3. Dynamic Font Scaling for 4K / HD
    font_size = int(h * 0.038)  # ~82px on 4K, ~41px on 1080p
    try:
        font = ImageFont.truetype("montserrat.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

    # 4. Phrase Chunking: Display current 4-word window
    chunk_size = 4
    current_chunk_idx = active_idx // chunk_size
    start_w_idx = current_chunk_idx * chunk_size
    end_w_idx = min(start_w_idx + chunk_size, len(words))
    
    display_words = words[start_w_idx:end_w_idx]
    display_text = " ".join(display_words)

    # Calculate bounding box dimensions
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center-Bottom Placement with Safe Margin
    start_x = (w - text_w) // 2
    start_y = int(h * 0.82)

    # 5. Draw Semi-Transparent Dark Background Plate (Netflix Style)
    padding_x = int(w * 0.015)
    padding_y = int(h * 0.008)
    rect_box = [
        start_x - padding_x,
        start_y - padding_y,
        start_x + text_w + padding_x,
        start_y + text_h + (padding_y * 2)
    ]
    # Draw dark translucent rectangle (R, G, B, Alpha)
    draw.rounded_rectangle(rect_box, radius=12, fill=(15, 18, 22, 190))

    # 6. Render Words with Active Highlight
    current_x = start_x
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    for relative_i, word in enumerate(display_words):
        actual_word_i = start_w_idx + relative_i
        word_w = draw.textbbox((0, 0), word, font=font)[2]
        
        # Color Logic: Active Word = Soft Gold/Yellow, Inactive = Crisp White
        if actual_word_i == active_idx:
            color = (255, 215, 0, 255)  # Gold
        else:
            color = (240, 240, 240, 230) # Off-white

        # Subtle Drop Shadow for Contrast
        draw.text((current_x + 2, start_y + 2), word, font=font, fill=(0, 0, 0, 180))
        draw.text((current_x, start_y), word, font=font, fill=color)
        
        current_x += word_w + space_w

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def apply_ken_burns_zoom(frame, t, duration, zoom_ratio=0.12):
    """Slow cinematic push-in motion (1.0x to 1.12x)."""
    h, w = frame.shape[:2]
    scale = 1.0 + (zoom_ratio * (t / max(duration, 0.1)))
    
    crop_w = int(w / scale)
    crop_h = int(h / scale)
    
    start_x = (w - crop_w) // 2
    start_y = (h - crop_h) // 2
    
    cropped = frame[start_y:start_y + crop_h, start_x:start_x + crop_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def apply_teal_and_orange_grade(frame):
    """Shifts shadows toward Teal and highlights toward Warm Orange."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_chan, a_chan, b_chan = cv2.split(lab)

    norm_l = l_chan / 255.0
    shadows = 1.0 - norm_l
    highlights = norm_l

    a_chan -= shadows * 6.0
    b_chan -= shadows * 10.0

    a_chan += highlights * 8.0
    b_chan += highlights * 12.0

    lab = cv2.merge([l_chan, np.clip(a_chan, 0, 255), np.clip(b_chan, 0, 255)])
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def apply_vignette_and_grain(frame, grain_intensity=10):
    """Applies edge shading and 35mm film grain."""
    h, w = frame.shape[:2]

    kernel_x = cv2.getGaussianKernel(w, w * 0.5)
    kernel_y = cv2.getGaussianKernel(h, h * 0.5)
    kernel = kernel_y * kernel_x.T
    vignette_mask = kernel / kernel.max()
    
    frame_float = frame.astype(np.float32)
    for i in range(3):
        frame_float[:, :, i] *= vignette_mask

    grain = np.random.normal(0, grain_intensity, (h, w, 3)).astype(np.float32)
    return np.clip(frame_float + grain, 0, 255).astype(np.uint8)


def apply_cinematic_vfx(frame, text, t, duration):
    """Complete Master Pipeline: Motion + Color Grade + Film Grain + Letterbox + BBC Subtitles."""
    # 1. Motion
    frame = apply_ken_burns_zoom(frame, t, duration)

    # 2. Color Grade
    frame = apply_teal_and_orange_grade(frame)

    # 3. Film Grain & Vignette
    frame = apply_vignette_and_grain(frame)

    # 4. 2.35:1 Letterbox Matte
    h, w = frame.shape[:2]
    bar_height = int((h - (w / 2.35)) / 2)
    if bar_height > 0:
        frame[:bar_height, :] = 0
        frame[h - bar_height:, :] = 0

    # 5. BBC / Netflix Subtitles
    frame = draw_netflix_style_subtitles(frame, text, t, duration)

    return frame