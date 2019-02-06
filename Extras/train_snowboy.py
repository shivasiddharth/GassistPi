from sys import byteorder
from array import array
from struct import pack
import base64
import requests
import time
import pyaudio
import wave

endpoint = "https://snowboy.kitt.ai/api/v1/train/"


############# MODIFY THE FOLLOWING #############
token = "ENTER_YOUR_SNOWBOY_TOKEN_HERE"
hotword_name = "ENTER_A_NAME_FOR_YOUR_HOTWORD" #Do not add ".pmdl" in the name
language = "en"
#ar (Arabic), zh (Chinese), nl (Dutch), en (English), fr (French), dt (German), hi (Hindi), it (Italian),
#jp (Japanese), ko (Korean), fa (Persian), pl (Polish), pt (Portuguese), ru (Russian), es (Spanish), ot (Other)
age_group = "20_29"
#0_9, 10_19, 20_29, 30_39, 40_49, 50_59, 60+
gender = "M"
#F/M
microphone = "Raspberry Pi microphone"
############### END OF MODIFY ##################

modelfilename="/home/{USER}/GassistPi/src/resources/"+hotword_name+".pmdl"

THRESHOLD = 1000
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in range(int(seconds*RATE))])
    r.extend(snd_data)
    r.extend([0 for i in range(int(seconds*RATE))])
    return r

def record():
    """
    Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure VLC et al can play
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 200:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()
    return True

def get_wave(fname):
    with open(fname) as infile:
        return base64.b64encode(infile.read())

def record_hotword_samples():
    for i in range(1,4):
        filename=str(i)+".wav"
        filepath="/tmp/"+filename
        print("Starting to record sample "+str(i)+" for training model.")
        print("Say out the hotword........")
        while not record_to_file(filepath):
            time.sleep(.1)
    return True

def train_snowboy_model():
    while not record_hotword_samples():
        time.sleep(.1)
    data = {
        "name": hotword_name,
        "language": language,
        "age_group": age_group,
        "gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave('/tmp/1.wav')},
            {"wave": get_wave('/tmp/2.wav')},
            {"wave": get_wave('/tmp/3.wav')}
        ]
    }
    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(modelfilename, "w") as outfile:
            outfile.write(response.content)
        print("Saved model to '%s'." % modelfilename)
    else:
        print("Request failed.")
        print(response.text)

if __name__ == "__main__":
    if token!="ENTER_YOUR_SNOWBOY_TOKEN_HERE" and hotword_name!="ENTER_A_NAME_FOR_YOUR_HOTWORD":
        train_snowboy_model()
    else:
        print("Please check your Snowboy token value and hotword model name")
