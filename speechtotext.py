import os
from google.cloud import storage
import json
import io
from google.cloud import speech
import subprocess
from pydub.utils import mediainfo
import subprocess
import math
import datetime
import srt

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="active-guild-395117-9e1d030b7f0d.json"

def video_info(video_filepath):
    """ this function returns number of channels, bit rate, and sample rate of the video"""

    video_data = mediainfo(video_filepath)
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate

def video_to_audio(video_filepath, audio_filename, video_channels, video_bit_rate, video_sample_rate):
    command = f"ffmpeg -i {video_filepath} -b:a {video_bit_rate} -ac {video_channels} -ar {video_sample_rate} -vn {audio_filename}"
    subprocess.call(command, shell=True)
    blob_name = f"audios/{audio_filename}"
    upload_blob("stt-bucket-01", audio_filename, blob_name)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    
    bucket_name = "my-stt-bucket-01"

    destination_blob_name = "audio"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

def long_running_recognize(storage_uri, channels, sample_rate):
    
    client = speech.SpeechClient()

    config = {
        "language_code": "ar",
        "sample_rate_hertz": int(sample_rate),
        "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "audio_channel_count": int(channels),
        "enable_word_time_offsets": True,
        "model": "Default",
        "enable_automatic_punctuation": False
    }
    # audio = {"uri": storage_uri}
    audio_path = "./audio.wav"

    # Load the audio file
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    operation = client.long_running_recognize(config=config, audio=audio)

    print(u"Waiting for operation to complete...")
    response = operation.result()
    print(operation)    
    return response

def subtitle_generation(response, bin_size=3):
    """We define a bin of time period to display the words in sync with audio. 
    Here, bin_size = 3 means each bin is of 3 secs. 
    All the words in the interval of 3 secs in result will be grouped togather."""
    transcriptions = []
    index = 0
    for result in response.results:
        try:
            if result.alternatives[0].words[0].start_time.seconds:
                # bin start -> for first word of result
                start_sec = result.alternatives[0].words[0].start_time.seconds 
                start_microsec = result.alternatives[0].words[0].start_time.nanos * 0.001
            else:
                # bin start -> For First word of response
                start_sec = 0
                start_microsec = 0 
            end_sec = start_sec + bin_size # bin end sec
            
            # for last word of result
            last_word_end_sec = result.alternatives[0].words[-1].end_tissh-keygen -t ed25519 -C me.seconds
            print(result.alternatives[0].words[-1].end_time) 
            last_word_end_microsec = result.alternatives[0].words[-1].end_time.nanos * 0.001
            
            # bin transcript
            transcript = result.alternatives[0].words[0].word
            
            index += 1 # subtitle index

            for i in range(len(result.alternatives[0].words) - 1):
                try:
                    word = result.alternatives[0].words[i + 1].word
                    word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
                    word_start_microsec = result.alternatives[0].words[i + 1].start_time.nanos * 0.001 # 0.001 to convert nana -> micro
                    word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
                    word_end_microsec = result.alternatives[0].words[i + 1].end_time.nanos * 0.001

                    if word_end_sec < end_sec:
                        transcript = transcript + " " + word
                    else:
                        previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
                        previous_word_end_microsec = result.alternatives[0].words[i].end_time.nanos * 0.001
                        
                        # append bin transcript
                        transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, previous_word_end_sec, previous_word_end_microsec), transcript))
                        
                        # reset bin parameters
                        start_sec = word_start_sec
                        start_microsec = word_start_microsec
                        end_sec = start_sec + bin_size
                        transcript = result.alternatives[0].words[i + 1].word
                        
                        index += 1
                except IndexError:
                    pass
            # append transcript of last transcript in bin
            transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, last_word_end_sec, last_word_end_microsec), transcript))
            index += 1
        except IndexError:
            pass
    
    # turn transcription list into subtitles
    # subtitles = srt.compose(transcript)
    return subtitles

def main():
    source_file_name = "sourcefile"
    video_path = "./video.mp4"
    # channels, bit_rate, sample_rate = video_info(video_path)
    audio_path = "./audio.wav"
    audio_info = mediainfo(audio_path)

    # Extract desired information
    channels = audio_info['channels']
    bit_rate = audio_info['bit_rate']
    sample_rate = audio_info['sample_rate']

    # print(channels, bit_rate, sample_rate)
    # blob_name=video_to_audio(video_path, "audio.wav", channels, bit_rate, sample_rate)
    # print(blob_name)
    # print("hello world")
    storage_url = "gs://my-stt-bucket-01/audio"
    response = long_running_recognize(storage_url, channels, sample_rate)
    print(response)
    subtitles= subtitle_generation(response)
    # with open("subtitles.srt", "w") as f:
    #     f.write(subtitles)

if __name__ == "__main__":
    main()