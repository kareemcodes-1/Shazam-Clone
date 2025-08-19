
import os
import json
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import shutil
import subprocess
import json

from app.services.spotify import SpotifyClient
from app.services.youtube import build_search_query, search_youtube_one, download_best_audio
from app.services.database import MongoDatabase

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:5173",
    "localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_URI = os.getenv("MONGO_URI")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MAX_AUDIO_DURATION_SEC = int(os.getenv("MAX_AUDIO_DURATION_SEC", "0") or 0) or None

FPCALC_PATH = os.getenv("FPCALC_PATH", "fpcalc")

spotify = SpotifyClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
store = MongoDatabase(MONGO_URI, MONGO_DB_NAME)

class AddSongIn(BaseModel):
    spotify_url: str


def _popcount32(x: int) -> int:
    x &= 0xFFFFFFFF

    return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")


def _hamming_similarity_seq(a: list[int], b: list[int]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    total_sim = 0.0
    for i in range(n):
        hd = _popcount32(a[i] ^ b[i])
        total_sim += 1.0 - (hd / 32.0)
    return total_sim / n


def fingerprint_similarity_offset(
    clip_fp: list[int],
    song_fp: list[int],
    *,
    window: int | None = None,
    step: int = 1,
) -> float:
    if not clip_fp or not song_fp:
        return 0.0

    if len(clip_fp) > len(song_fp):
        clip_fp, song_fp = song_fp, clip_fp

    clip_len = len(clip_fp)
    if window is None:
        window = clip_len
    window = max(min(window, clip_len), 32)

    best = 0.0
    clip_start = max(0, clip_len - window)
    clip_seg = clip_fp[clip_start:clip_start + window]

    max_offset = len(song_fp) - window
    if max_offset < 0:
        return _hamming_similarity_seq(clip_seg[:len(song_fp)], song_fp[:len(clip_seg)])

    for off in range(0, max_offset + 1, step):
        song_seg = song_fp[off:off + window]
        sim = _hamming_similarity_seq(clip_seg, song_seg)
        if sim > best:
            best = sim
            if best >= 0.98:
                break
    return best


def generate_fingerprint(file_path):
    try:
        result = subprocess.run(
            ["fpcalc", "-raw", "-json", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        fingerprint_list = data["fingerprint"]

        return fingerprint_list

    except Exception as e:
        raise RuntimeError(f"Error generating fingerprint: {e}")


def fingerprint_similarity(fp1, fp2, tolerance=1):
    if not fp1 or not fp2:
        return 0.0
    if len(fp1) > len(fp2):
        fp1, fp2 = fp2, fp1

    max_score = 0.0


    for offset in range(len(fp2) - len(fp1) + 1):
        matches = sum(
            1 for i in range(len(fp1))
            if abs(fp1[i] - fp2[i + offset]) <= tolerance
        )
        score = matches / len(fp1)
        max_score = max(max_score, score)

        if max_score == 1.0:
            break

    return max_score







def find_song_match(audio_path: str):

    recorded_fp = generate_fingerprint(audio_path)

    if not recorded_fp:
        return None

    best_match = None
    best_score = 0.0

    ACCEPT_THRESHOLD = 0.55

    STEP = 1 if len(recorded_fp) < 400 else 2

    for song in store.songs.find({}, {"fingerprint": 1, "meta": 1}):
        song_fp = song.get("fingerprint", [])
        if not song_fp:
            continue

        score = fingerprint_similarity_offset(
            recorded_fp,
            song_fp,
            window=None,
            step=STEP,
        )
        # logging.debug(
        #     f"Comparing against {song['meta']['title']} "
        #     f"(clip_len={len(recorded_fp)}, song_len={len(song_fp)}, score={score:.4f})"
        # )

        if score > best_score:
            best_score = score
            best_match = song

    if best_match and best_score >= ACCEPT_THRESHOLD:
        # logging.info(f"Match: {best_match['meta']['title']} (score={best_score:.4f})")
        return best_match["meta"]

    # logging.info(f"No match. Best score={best_score:.4f}")




# ----------------------
# Add Song endpoint
# ----------------------
@app.post("/add-song")
def add_song(body: AddSongIn):
    track_id = spotify.extract_track_id(body.spotify_url)
    if not track_id:
        raise HTTPException(status_code=400, detail="Invalid Spotify track URL/URI")

    try:
        meta = spotify.get_track(track_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Spotify error: {e}")

    query = build_search_query(meta["title"], meta["artist"], meta.get("album"))
    yt_url = search_youtube_one(query)
    if not yt_url:
        raise HTTPException(status_code=404, detail="No YouTube match found")

    try:
        out_dir = "downloads"
        audio_path, info = download_best_audio(yt_url, out_dir, MAX_AUDIO_DURATION_SEC)

        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="Download succeeded but file not found on disk")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download error: {e}")

    try:
        fingerprint = generate_fingerprint(audio_path)
        doc_id = store.save_song(
            meta=meta,
            audio_path=audio_path,
            youtube_url=yt_url,
            fingerprint=fingerprint,
            content_type="audio/m4a"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB save error: {e}")

    return {"id": doc_id, "meta": meta, "youtube_url": yt_url}


# ----------------------
# Recognize Audio endpoint
# ----------------------
@app.post("/audio/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    tmp_path = None
    processed_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Save a copy for manual listening
        received_copy = os.path.join(os.getcwd(), "received.wav")
        shutil.copy(tmp_path, received_copy)
        processed_path = tmp_path.replace(".wav", "_processed.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp_path,
            "-ac", "1", "-ar", "16000", processed_path
        ], check=True)

        match = find_song_match(processed_path)

        if not match:
            raise HTTPException(status_code=404, detail="No match found")
        return {"match": match}

    except HTTPException:
        raise
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (tmp_path, processed_path):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                print("Failed to remove temporary file: %s", p, exc_info=True)

