import os
from typing import Dict, Any
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime

class MongoDatabase:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.fs = GridFS(self.db)
        self.songs = self.db["songs"]

    def save_song(
    self,
    meta: Dict[str, Any],
    audio_path: str,
    youtube_url: str,
    fingerprint: list[int],
    content_type: str = "audio/mp4",  # changed from m4a → mp4
) -> str:


        # Store audio in GridFS
        with open(audio_path, "rb") as f:
            file_id = self.fs.put(
                f,
                filename=os.path.basename(audio_path),
                contentType=content_type
            )

        doc = {
            "meta": meta,
            "youtube_url": youtube_url,
            "fingerprint": fingerprint,
            "audio_file_id": file_id,
            "created_at": datetime.now(),
        }
        res = self.songs.insert_one(doc)
        return str(res.inserted_id)

    def get_song(self, _id):
        from bson import ObjectId
        return self.songs.find_one({"_id": ObjectId(_id)})

    def stream_audio(self, file_id):
        from bson import ObjectId
        return self.fs.get(ObjectId(file_id))
