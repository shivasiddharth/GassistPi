"""
Estimate the magnitude squared coherence estimate,

- requirements
    sudo apt install python-numpy python-scipy python-matplotlib
"""


import sys
import wave
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print('Usage: python {} audio.wav'.format(sys.argv[0]))
    sys.exit(1)

wav = wave.open(sys.argv[1], 'rb')
channels = wav.getnchannels()
frames = wav.readframes(wav.getnframes())
fs = wav.getframerate()
wav.close()

print("channels: %d" % channels)
print("rate    : %d" % fs)
print("frames  : %d" % wav.getnframes())

array = np.fromstring(frames, dtype='int16')

ch0 = array[0::channels]

fig, ax = plt.subplots()

for ch in range(1, channels):
    f, c = signal.coherence(ch0, array[ch::channels], fs, nperseg=1024)
    ax.semilogy(f, c, label="CO 1-%d" % (ch + 1))

legend = ax.legend(loc='lower right', shadow=True, fontsize='small')

plt.xlabel('frequency [Hz]')
plt.ylabel('Coherence')
plt.show()

