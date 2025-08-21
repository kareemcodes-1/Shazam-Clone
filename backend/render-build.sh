#!/usr/bin/env bash
set -o errexit  # Exit on error

# Install system dependencies
apt-get update
apt-get install -y ffmpeg chromaprint
