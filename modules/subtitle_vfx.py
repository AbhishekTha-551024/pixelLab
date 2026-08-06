import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── COLOR GRADE PRESETS ─────────────────────────────────────
def apply_color_grade(frame, config):
    grade = config.get("color_grade", "None")
    sat   = config.get("saturation", 1.0)
    alpha = config.get("contrast", 1.05)
    beta  = config.get("brightness", 2)

    # Base brightness/contrast
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Saturation via HSV
    if sat != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    # Grade presets
    if grade == "Cinematic Teal & Orange":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.1 + 10, 0, 255).astype(np.uint8)
        g = np.clip(lut * 0.95, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.85, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Warm Sunset":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.15 + 15, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.80, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Cold Blue Steel":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 0.82, 0, 255).astype(np.uint8)
        b = np.clip(lut * 1.20 + 10, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Vintage Film":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.08 + 8, 0, 255).astype(np.uint8)
        g = np.clip(lut * 1.02 + 5, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.78 + 20, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "High Contrast B&W":
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=-20)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif grade == "Moody Dark":
        frame = cv2.convertScaleAbs(frame, alpha=0.80, beta=-15)

    elif grade == "Vibrant Pop":
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)

    elif grade == "Golden Hour":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.20 + 20, 0, 255).astype(np.uint8)
        g = np.clip(lut * 1.05 + 5, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.70, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    return frame


# ── VIGNETTE ───────────────────────────────────────────────
def apply_vignette(frame, strength):
    if strength <= 0:
        return frame
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    mask = 1 - np.clip(dist * strength, 0, 1)
    mask = mask[:, :, np.newaxis]
    return np.clip(frame * mask, 0, 255).astype(np.uint8)


# ── FILM GRAIN ─────────────────────────────────────────────
def apply_grain(frame, intensity):
    if intensity <= 0:
        return frame
    noise = np.random.normal(0, intensity * 25, frame.shape).astype(np.int16)
    return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)


# ── LETTERBOX ──────────────────────────────────────────────
def apply_letterbox(frame, ratio_str):
    h, w = frame.shape[:2]
    ratio_map = {
        "2.35:1 (Anamorphic)": 2.35,
        "2.39:1 (Ultra Scope)": 2.39,
        "1.85:1 (Flat)": 1.85,
    }
    ratio = ratio_map.get(ratio_str, 2.35)
    bar_h = int((h - (w / ratio)) / 2)
    if bar_h > 0:
        frame[:bar_h, :] = 0
        frame[h - bar_h:, :] = 0
    return frame


# ── SUBTITLE COLOR STYLES ──────────────────────────────────
SUBTITLE_STYLES = {
    "Kinetic Yellow":   {"active": (255, 235, 59),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Cyberpunk Neon":   {"active": (0, 255, 255),   "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": (255, 0, 128)},
    "Clean Classic":    {"active": (255, 255, 255),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Boxed Background": {"active": (255, 235, 59),   "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Fire Red":         {"active": (255, 60, 30),    "inactive": (255, 220, 200), "stroke": (80, 0, 0),      "stroke_active": None},
    "Instagram White":  {"active": (255, 255, 255),  "inactive": (200, 200, 200), "stroke": (0, 0, 0),       "stroke_active": None},
    "MrBeast Bold":     {"active": (255, 220, 0),    "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": (200, 0, 0)},
    "Gradient Rainbow": {"active": (255, 100, 255),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Minimal Fade":     {"active": (255, 255, 255),  "inactive": (180, 180, 180), "stroke": (30, 30, 30),    "stroke_active": None},
}

SIZE_MAP = {
    "Tiny": 0.025, "Small": 0.038, "Medium": 0.055,
    "Large": 0.072, "Extra Large": 0.090, "Massive": 0.115
}

POS_MAP = {
    "Bottom": 0.83, "Lower Center": 0.72, "Center": 0.47,
    "Upper Center": 0.28, "Top": 0.10
}


def draw_kinetic_subtitles(frame, text, t, duration, config):
    if not text or not text.strip():
        return frame

    h, w = frame.shape[:2]
    words = text.split()
    if not words:
        return frame

    progress   = max(0, min(1, t / max(duration, 0.1)))
    active_idx = min(int(progress * len(words)), len(words) - 1)

    img  = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    font_size = max(20, int(h * SIZE_MAP.get(config.get("size", "Medium"), 0.055)))
    font_file = config.get("font", "DejaVuSans-Bold.ttf")
    try:
        font = ImageFont.truetype(font_file, font_size)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

    start_y  = int(h * POS_MAP.get(config.get("position", "Bottom"), 0.83))
    total_text = " ".join(words)
    bbox     = draw.textbbox((0, 0), total_text, font=font)
    text_w   = bbox[2] - bbox[0]
    text_h   = bbox[3] - bbox[1]

    alignment = config.get("alignment", "Center")
    if alignment == "Center":
        start_x = max(20, (w - text_w) // 2)
    elif alignment == "Left":
        start_x = 40
    else:
        start_x = max(20, w - text_w - 40)

    style_def = SUBTITLE_STYLES.get(config.get("style", "Kinetic Yellow"), SUBTITLE_STYLES["Kinetic Yellow"])
    stroke_r  = max(1, config.get("stroke_width", 3))

    # Boxed Background
    if config.get("style") in ("Boxed Background", "MrBeast Bold", "Instagram White"):
        px, py = 22, 14
        draw.rectangle([
            max(8, start_x - px), start_y - py,
            min(w - 8, start_x + text_w + px), start_y + text_h + py
        ], fill=(0, 0, 0, 160))

    space_w   = draw.textbbox((0, 0), " ", font=font)[2]
    current_x = start_x
    animation = config.get("animation", "Active Word Highlight")

    for idx, word in enumerate(words):
        word_w = draw.textbbox((0, 0), word, font=font)[2]
        is_active = (idx == active_idx)

        # Choose color based on animation style
        if animation == "All White (No Animation)":
            color = (255, 255, 255)
        elif animation == "Fade In Words":
            alpha_val = 255 if idx <= active_idx else 80
            color = style_def["active"][:3] + (alpha_val,) if is_active else (200, 200, 200, alpha_val)
            color = color[:3]  # PIL draw.text needs RGB for stroke pass
        else:
            color = style_def["active"] if is_active else style_def["inactive"]

        stroke_col = style_def.get("stroke_active") if (is_active and style_def.get("stroke_active")) else style_def["stroke"]

        # Stroke
        for sx in range(-stroke_r, stroke_r + 1):
            for sy in range(-stroke_r, stroke_r + 1):
                if sx != 0 or sy != 0:
                    draw.text((current_x + sx, start_y + sy), word, font=font, fill=stroke_col)

        # Scale Pop animation: active word slightly bigger (re-draw at offset)
        if animation == "Scale Pop" and is_active:
            try:
                big_font = ImageFont.truetype(font_file, int(font_size * 1.25))
                draw.text((current_x - 3, start_y - 5), word, font=big_font, fill=color)
            except Exception:
                draw.text((current_x, start_y), word, font=font, fill=color)
        elif animation == "Karaoke Underline" and is_active:
            draw.text((current_x, start_y), word, font=font, fill=color)
            draw.rectangle([current_x, start_y + text_h + 3, current_x + word_w, start_y + text_h + 7],
                           fill=style_def["active"])
        else:
            draw.text((current_x, start_y), word, font=font, fill=color)

        current_x += word_w + space_w

    return np.array(img.convert("RGB"))


def apply_cinematic_vfx(frame, text, t, duration, config):
    """Master VFX pipeline — runs all effects in order."""

    # 1. Color grade + brightness/contrast/saturation
    frame = apply_color_grade(frame, config)

    # 2. Vignette
    frame = apply_vignette(frame, config.get("vignette", 0.0))

    # 3. Film grain
    frame = apply_grain(frame, config.get("grain_intensity", 0.0))

    # 4. Letterbox
    if config.get("enable_letterbox"):
        frame = apply_letterbox(frame, config.get("letterbox_ratio", "2.35:1 (Anamorphic)"))

    # 5. Subtitles
    frame = draw_kinetic_subtitles(frame, text, t, duration, config)

    return frame