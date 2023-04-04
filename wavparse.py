import numpy as np
import wave
import struct
import sys

sampleRate = 48000  # hertz
val = 32767

Space = np.zeros(int(sampleRate/1200), dtype=np.int16).tobytes()
Zero = np.hstack([v*np.ones(int(sampleRate/1200/2), dtype=np.int16)
                 for v in [val, -val]]).tobytes()
One = np.hstack([v*np.ones(int(sampleRate/1200/4), dtype=np.int16)
                for v in [val, -val, val, -val]]).tobytes()
conv = {' ': Space, '0': Zero, '1': One}


def writeWavFromBs(filename, data):
    obj = wave.open(filename, 'wb')
    obj.setnchannels(1)  # mono
    obj.setsampwidth(2)
    obj.setframerate(sampleRate)
    obj.writeframesraw(Space)
    for d in data:
        obj.writeframesraw(conv[d])
    obj.close()


def writeWav(filename, d):
    obj = wave.open(filename, 'wb')
    obj.setnchannels(1)  # mono
    obj.setsampwidth(2)
    obj.setframerate(d["bitrate"])
    obj.writeframesraw(Space)
    for d in d["signal"]:
        obj.writeframesraw(np.int16(val*d))
    obj.close()


def bittowav(filename):
    with open(filename) as f:
        data = f.read()
        outname = ".".join(filename.split(".")[:-1])+".wav"
        writeWav(outname, data)
        print("Wrote", outname)
