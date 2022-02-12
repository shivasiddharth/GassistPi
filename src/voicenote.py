#from matplotlib import pyplot as plt
#import numpy as np
from sys import byteorder
from array import array
from struct import pack
import audioop
import pyaudio
import wave


THRESHOLD = 1000
CHUNK_SIZE = 4096
FORMAT = pyaudio.paInt16
RATE = 44100


def check_validity(snd_data):
    """
    Returns 0 if the mean value of snd_data is between
    100 and 300, 
    If the value is smaller than 100, it returns -1
    else cases, it returns +1
    """
    rms_value = audioop.rms(snd_data, 2)
    if 98 <= max(snd_data) <= 300:
        return 0
    elif max(snd_data) > 300:
        # Apply moving average method
        if rms_value < 300:
            return 0
        return 1
    else:
        return -1


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
            if not snd_started and abs(i) > THRESHOLD:
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
    stream = p.open(format=FORMAT, 
                    channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False
    r = array('h')

    # Plot wave setting
   # _, ax = plt.subplots(figsize=(14, 6))
   # x = np.arange(0, 2 * CHUNK_SIZE, 2)
   # ax.set_ylim(-500, 500)
   # ax.set_xlim(0, CHUNK_SIZE)  # make sure our x axis matched our chunk size
   # line, = ax.plot(x, np.random.rand(CHUNK_SIZE))

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()

        # Plot data
      #  data = np.asarray(snd_data, np.int16)
      #  line.set_ydata(data)
      #  plt.pause(0.01)

        print("Testing ===> num_silent:{},\tmax_value:{}, \tlength:{}".format(
            num_silent, max(snd_data), len(snd_data)))

        result = check_validity(snd_data)
        if result == 0:
            snd_started = True
            r.extend(snd_data)
        elif result == 1:
            continue
        else:
            if snd_started:
                num_silent += 1
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


if __name__ == '__main__':
    print("please speak a word into the microphone")
    record_to_file('demo.wav')
    print("done - result written to demo.wav")
