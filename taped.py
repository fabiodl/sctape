import sys
from audioparse import readAudio
from tzxparse import readTzx
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt


hs=44100
def plotAudio(fname):
    fr,y=readAudio(fname)
    y=signal.resample(y,int(np.ceil(len(y)*hs/fr)))
    y=y/np.max(np.abs(y))
    print("audio",len(y),"samples fr=",fr)
    plt.plot(y)


def plotTzx(fname):
    y=readTzx(fname)["signal"]
    print("tzx",len(y),"samples")
    plt.plot(y)

    
if __name__=="__main__":

    if len(sys.argv)>1:
        plotAudio(sys.argv[1])

    if len(sys.argv)>2:
        plotTzx(sys.argv[2])

    plt.show()
