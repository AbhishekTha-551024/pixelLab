import os
import requests
from config import PIXABAY_API_KEY, TEMP_DIR

def get_stock_clip(search_query, index):
    """
    Fetches HD stock footage from Pixabay based on search query.
    
    Args:
        search_query (str): Keyword for stock video search.
        index (int): Scene index number for structured naming.
        
    Returns:
        str or None: Path to downloaded video clip or None if failed.
    """
    filename = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_query}&min_width=1280&per_page=5"

    try:
        res = requests.get(url, timeout=10).json()
        hits = res.get("hits", [])

        # Fallback search query if initial search yields 0 hits
        if not hits:
            fallback_url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q=cinematic&min_width=1280&per_page=5"
            res = requests.get(fallback_url, timeout=10).json()
            hits = res.get("hits", [])

        if hits:
            v_info = hits[0].get("videos", {})
            # Prioritize resolution: Large (1080p) -> Medium (720p) -> Small
            download_url = (
                v_info.get("large", {}).get("url")
                or v_info.get("medium", {}).get("url")
                or v_info.get("small", {}).get("url")
            )

            if download_url:
                res_video = requests.get(download_url, stream=True, timeout=15)
                with open(filename, "wb") as f:
                    for chunk in res_video.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return filename
    except Exception as e:
        print(f"❌ Stock download error for query '{search_query}': {e}")

    return None