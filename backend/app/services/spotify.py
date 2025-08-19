import os
import re
import base64
import requests
from typing import Dict, Optional

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_TRACK_URL = "https://api.spotify.com/v1/tracks/{}"
SPOTIFY_LINK_RE = re.compile(
    r"(?:https?://open\.spotify\.com/track/|spotify:track:)([a-zA-Z0-9]+)"
)

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None

    def _get_access_token(self) -> str:
        if self._token:
            return self._token
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}
        resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=15)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def extract_track_id(self, url_or_uri: str) -> Optional[str]:
        m = SPOTIFY_LINK_RE.search(url_or_uri.strip())
        return m.group(1) if m else None

    def get_track(self, track_id: str) -> Dict:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(SPOTIFY_TRACK_URL.format(track_id), headers=headers, timeout=15)
        resp.raise_for_status()
        d = resp.json()

        artists = ", ".join(a["name"] for a in d.get("artists", []))
        images = d.get("album", {}).get("images", [])
        album_cover = images[0]["url"] if images else None

        return {
            "spotify_track_id": d.get("id"),
            "title": d.get("name"),
            "artist": artists,
            "album": d.get("album", {}).get("name"),
            "release_date": d.get("album", {}).get("release_date"),
            "duration_ms": d.get("duration_ms"),
            "spotify_url": d.get("external_urls", {}).get("spotify"),
            "album_cover": album_cover,
        }