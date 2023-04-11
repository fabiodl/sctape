import sys
import numpy as np
import itertools


def bigEndian(x):
    return np.sum([v*(256**i) for i, v in enumerate(x[::-1])])


def le(d):
    return sum([c << (8*i) for i, c in enumerate(d)])


def hexString(x):
    return " ".join([f"{v:02X}" for v in x])


def leint(x, n):
    l = []
    for i in range(n):
        l.append(x & 0xFF)
        x = x >> 8
    return l


def beint(x, n):
    l = []
    for i in range(n):
        l.append((x >> ((n-1-i)*8)) & 0xFF)
    return l

# https://stackoverflow.com/questions/1066758/find-length-of-sequences-of-identical-values-in-a-numpy-array-run-length-encodi/32681075


def lre(bits):
    for bit, group in itertools.groupby(bits):
        yield (bit, len(list(group)))


def printable(s):
    return "".join([c for c in s if c.isprintable()])


def getParam(index, default):
    if len(sys.argv) > index:
        return sys.argv[index]
    return default


def removeExtension(filename):
    return ".".join(filename.split(".")[:-1])


def rhoSweep(func, filename, rho, opts):
    if rho == "auto":
        for div in range(1, 8):
            s = 1.0/2**div
            for rho in np.arange(s, 1, 2*s):
                try:
                    print(f"Level at {rho:0.2f}")
                    d = func(filename, rho, rho, opts)
                    print(f"\nOK for {rho:0.2f}")
                    return d
                except Exception as e:
                    print(f"Level at {rho:0.2f} failed:"+str(e))
                    print("")
                    # raise
        raise Exception("No level found")
    else:
        return func(filename, rho, rho, opts)


def rhoSweepMax(func, filename, opts):
    best = -1
    bestd = None
    for div in range(1, int(opts.get("search_precision", 8))):
        s = 1.0/2**div
        for rho in np.arange(s, 1, 2*s):
            try:
                print(f"Level at {rho:0.2f}", end=" ")
                score, d = func(filename, rho, rho, opts)
                print(f"score {score:.2f} max {best:.2f}")
                if score > best:
                    best = score
                    bestd = d
            except Exception as e:
                print(f"Level at {rho:0.2f} failed:"+str(e))
                print("")
                # raise
    return bestd
