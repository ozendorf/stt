#!/bin/bash
video_url=$1
video_id=$(( RANDOM % 10000 ))
video_path="video$video_id.mp4"

youtube-dl $1 -o $video_path
audio_path="audio$video_id.wav"
ffmpeg -i $video_path $audio_path
python speechtotext.py "./$video_path" "./$audio_path"
