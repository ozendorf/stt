import os
import ffmpeg
import sys
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
import glob

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="active-guild-395117-9e1d030b7f0d.json"

def video_info(video_filepath):
    """ this function returns number of channels, bit rate, and sample rate of the video"""

    video_data = mediainfo(video_filepath)
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate

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

def long_running_recognize(storage_uri, channels, sample_rate, audio_path):
    
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

    # Load the audio file
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    operation = client.long_running_recognize(config=config, audio=audio)

    print(u"Waiting for operation to complete...")
    response = operation.result()
    return response

def subtitle_generation(response, bin_size=3):
    """We define a bin of time period to display the words in sync with audio. 
    Here, bin_size = 3 means each bin is of 3 secs. 
    All the words in the interval of 3 secs in result will be grouped togather."""
    transcriptions = []
    index = 0
    for result in response.results:
        print("results: " + str(result))
        try:
            if result.alternatives[0].words[0].start_time.seconds:
                # bin start -> for first word of result
                start_sec = result.alternatives[0].words[0].start_time.seconds 
                start_microsec = result.alternatives[0].words[0].start_time.microseconds
            else:
                # bin start -> For First word of response
                start_sec = 0
                start_microsec = 0 
            end_sec = start_sec + bin_size # bin end sec
            
            # for last word of result
            last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
            print("last_word_end_sec: " + str(result.alternatives[0].words[-1].end_time.seconds)) 
            last_word_end_microsec = result.alternatives[0].words[-1].end_time.microseconds
        # bin transcript
            transcript = result.alternatives[0].words[0].word
            
            index += 1 # subtitle index

            for i in range(len(result.alternatives[0].words) - 1):
                try:
                    word = result.alternatives[0].words[i + 1].word
                    word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
                    word_start_microsec = result.alternatives[0].words[i + 1].start_time.microseconds # 0.001 to convert nana -> micro
                    word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
                    word_end_microsec = result.alternatives[0].words[i + 1].end_time.microseconds

                    if word_end_sec < end_sec:
                        transcript = transcript + " " + word
                    else:
                        previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
                        previous_word_end_microsec = result.alternatives[0].words[i].end_time.microseconds
                        
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
        # print(transcript)
        subtitles = srt.compose(transcriptions)
        print(subtitles)
    return subtitles

def main(video_path, audio_path):

    source_file_name = "sourcefile"
    channels, bit_rate, sample_rate = video_info(video_path)
    audio_info = mediainfo(video_path)

    # Extract desired information
    channels = audio_info['channels']
    bit_rate = audio_info['bit_rate']
    sample_rate = audio_info['sample_rate']

    storage_url = "gs://my-stt-bucket-01/audio"

    split_command = [
    'ffmpeg',
    '-i',
    audio_path,
    '-f',
    'segment',
    '-segment_time',
    '30',
    '-c',
    'copy',
    'splitted-'+audio_path+'-%03d.wav'
    ]

# Execute the command
    subprocess.run(split_command)


    directory_path = './'
    string_pattern = 'splitted-'+audio_path+'*'  # For example, to match all files with a .txt extension

    # Use glob to find files that match the specified pattern
    matching_files = glob.glob(directory_path + '/' + string_pattern)

    # Loop through the matching files
    i = 000
    for file_name in matching_files:
        print(file_name)  
        response = long_running_recognize(storage_url, channels, sample_rate, file_name)
        subtitles = str(subtitle_generation(response))
        with open("subtitles"+audio_path+str(i)+".srt", "w") as f:
            f.write(subtitles)
        i += 1
if __name__ == "__main__":
    video_path = sys.argv[1]
    audio_path = sys.argv[2]
        
    main(video_path, audio_path)
