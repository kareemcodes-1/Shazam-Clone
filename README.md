🎵 Shazam Clone

A simple Shazam-like app where you can identify songs by recording audio and matching it against saved tracks. Built with a custom audio fingerprinting approach inspired by how Shazam works.

🚀 How It Works

Add Songs

Copy a Spotify song link.

Paste it into the input field on the website.

The song is saved to the database with its fingerprint.

Record & Identify

Click the Record button on the frontend.

Play the song (from your laptop, phone, or speakers).

The app records the snippet and sends it to the backend.

Audio Processing

The backend converts the recording into a spectrogram.

It reduces frequencies to extract the peaks (unique identifiers of the track).

A fingerprint is generated for the recording.

Matching & Prediction

The new fingerprint is compared against stored fingerprints in the database.

The app calculates similarity scores.

The best match is returned as the predicted song.

🛠 Tech Stack

Frontend: React.js

Backend: FastAPI / Node.js

Database: MongoDB

Audio Processing: FFmpeg + Custom Fingerprinting Algorithm (fpcalc)

✨ Features

Save songs via Spotify links

Record live audio to identify tracks

Custom fingerprinting for song matching

Returns best match with similarity score
