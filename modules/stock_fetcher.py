import os
import requests
from config import PIXABAY_API_KEY, TEMP_DIR

def get_stock_clip(search_query, index):
    """Pixabay से 4K (Large) हाई-क्वालिटी स्टॉक वीडियो डाउनलोड करता है।"""
    filename = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_query}&per_page=5"
    
    try:
        res = requests.get(url).json()
        hits = res.get("hits", [])
        if hits:
            v_info = hits[0].get("videos", {})
            # सबसे पहले 4K 'large' डाउनलोड करने की कोशिश करेगा
            d_url = (
                v_info.get("large", {}).get("url") or 
                v_info.get("medium", {}).get("url") or 
                v_info.get("small", {}).get("url")
            )
            if d_url:
                print(f"⬇️ Downloading Crisp 4K/HD stock clip for '{search_query}'...")
                res_video = requests.get(d_url, stream=True)
                with open(filename, "wb") as f:
                    for chunk in res_video.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                return filename
    except Exception as e:
        print(f"❌ Stock download error for '{search_query}': {e}")
    return None