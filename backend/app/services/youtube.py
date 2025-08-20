import os
from typing import Optional, Tuple
from yt_dlp import YoutubeDL
from yt_dlp.utils import match_filter_func

# Path where cookies file will be stored
COOKIES_PATH = os.getenv("YOUTUBE_COOKIES", "cookies.txt")

# If cookie content is passed via env var, write it to file
if os.getenv("YOUTUBE_COOKIES_CONTENT"):
    with open(COOKIES_PATH, "w", encoding="utf-8") as f:
        f.write(os.getenv("YOUTUBE_COOKIES_CONTENT"))

def build_search_query(title: str, artist: str, album: Optional[str] = None) -> str:
    parts = [title, artist]
    if album:
        parts.append(album)
    parts.append("audio")
    return " ".join(p for p in parts if p)

def search_youtube_one(query: str) -> Optional[str]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "cookiefile": COOKIES_PATH,  # ✅ will use file created above
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if "entries" in info and info["entries"]:
                return info["entries"][0]["webpage_url"]
    except Exception as e:
        print(f"[YouTube Search Error] {e}")
    return None

def download_best_audio(
    youtube_url: str,
    out_dir: str,
    max_duration_sec: Optional[int] = None
) -> Tuple[str, dict]:
    os.makedirs(out_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "cookiefile": COOKIES_PATH,  # ✅ will use file created above
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a"},
        ],
    }

    # Enable duration filtering if needed
    # if max_duration_sec is not None:
    #     ydl_opts["match_filter"] = match_filter_func(f"duration <= {max_duration_sec}")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        vid_id = info.get("id")
        m4a_path = os.path.join(out_dir, f"{vid_id}.m4a")
        final_path = m4a_path if os.path.exists(m4a_path) else ydl.prepare_filename(info)
        return final_path, info
