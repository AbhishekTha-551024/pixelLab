import os
import requests
from config import TEMP_DIR

def get_stock_clip(search_query, index):
    """
    Fetches HD stock footage from Pixabay based on search query.
    
    ✅ FIX #3: API key ab runtime pe os.environ se read hoti hai,
    config load hone ke time pe nahi — isliye app.py mein set kiya
    hua key yahan properly milega.
    """
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
    
    if not pixabay_key:
        print("❌ PIXABAY_API_KEY missing! Streamlit Secrets mein add karo.")
        return None

    filename = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")
    url = f"https://pixabay.com/api/videos/?key={pixabay_key}&q={search_query}&min_width=1280&per_page=5"

    try:
        res = requests.get(url, timeout=10).json()
        hits = res.get("hits", [])

        if not hits:
            print(f"⚠️ No results for '{search_query}', trying fallback 'cinematic'...")
            fallback_url = f"https://pixabay.com/api/videos/?key={pixabay_key}&q=cinematic&min_width=1280&per_page=5"
            res = requests.get(fallback_url, timeout=10).json()
            hits = res.get("hits", [])

        if hits:
            v_info = hits[0].get("videos", {})
            download_url = (
                v_info.get("large", {}).get("url")
                or v_info.get("medium", {}).get("url")
                or v_info.get("small", {}).get("url")
            )

            if download_url:
                res_video = requests.get(download_url, stream=True, timeout=30)
                with open(filename, "wb") as f:
                    for chunk in res_video.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                print(f"✅ Downloaded clip for '{search_query}'")
                return filename
            else:
                print(f"⚠️ No download URL found for '{search_query}'")
        else:
            print(f"⚠️ Pixabay returned 0 hits even for fallback query.")

    except Exception as e:
        print(f"❌ Stock download error for query '{search_query}': {e}")

    return None