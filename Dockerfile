FROM ubuntu:22.04

COPY ./requirements.txt /home/requirements.txt

RUN apt-get update \ 
  && apt-get install -y python3 \ 
  && apt install -y ffmpeg \
  && apt install -y pip \ 
  && pip install yt-dlp==2023.12.30 \ 
  && pip install -r /home/requirements.txt \
  && pip install google-cloud-storage==2.14.0

COPY docker-stt.sh /home/docker-stt.sh

COPY speechtotext.py /home/speechtotext.py

WORKDIR /home

COPY active-guild-395117-9e1d030b7f0d.json /home/active-guild-395117-9e1d030b7f0d.json
