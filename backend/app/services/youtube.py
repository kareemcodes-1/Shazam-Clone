import os
from typing import Optional, Tuple
from pytube import YouTube, Search


def build_search_query(title: str, artist: str, album: Optional[str] = None) -> str:
    parts = [title, artist]
    if album:
        parts.append(album)
    parts.append("audio")
    return " ".join(p for p in parts if p)


def search_youtube_one(query: str) -> Optional[str]:
    """Search YouTube using pytube and return the first video URL."""
    try:
        s = Search(query)
        results = s.results
        if results:
            return results[0].watch_url
    except Exception as e:
        print(f"[Pytube Search Error] {e}")
    return None


def download_best_audio(
    youtube_url: str,
    out_dir: str,
    max_duration_sec: Optional[int] = None
) -> Tuple[str, dict]:
    """Download the best available audio using pytube."""
    os.makedirs(out_dir, exist_ok=True)

    yt = YouTube(youtube_url)
    # Optional: check duration if max_duration_sec is provided
    if max_duration_sec and yt.length > max_duration_sec:
        raise ValueError(f"Video is too long ({yt.length}s > {max_duration_sec}s)")

    stream = yt.streams.filter(only_audio=True, file_extension="mp4").order_by("abr").desc().first()
    if not stream:
        raise RuntimeError("No suitable audio stream found")

    out_path = stream.download(output_path=out_dir, filename=f"{yt.video_id}.mp4")

    return out_path, {
        "title": yt.title,
        "author": yt.author,
        "length": yt.length,
        "views": yt.views,
        "video_id": yt.video_id,
        "watch_url": yt.watch_url,
    }
