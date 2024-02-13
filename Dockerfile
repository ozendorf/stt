FROM ubuntu:22.04

RUN apt-get update \ 
  && apt-get install -y python3 \ 
  && apt install -y ffmpeg \
  && apt install -y pip \ 
  && pip install yt-dlp \  

COPY ./stt.sh /stt.sh

COPY ./speechtotext.py /speechtotext.py

RUN sh stt.sh https://www.youtube.com/watch?v=u5Ef91rJGBQ