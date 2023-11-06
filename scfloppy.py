#! /usr/bin/env python3

import sys
import os
import pathlib
import getopt
from inspect import signature
import math

TRACKS = 40
SECTORSIZE = 256
SECTORSPERCLUSTER = 4
SECTORSPERTRACK = 16
CLUSTERSPERTRACK = 4


DIRTRACK = 20
DIRSECTOR = 0
DIRENTRYLEN = 16
DIRENTRYNUM = 192
FATTRACK = 20
FATSECTOR = 12


class Floppy:

    def __init_(self):
        self.format()

    def open(self, filename):
        self.filename = filename
        self.data = bytearray(open(filename, "rb").read())
        if len(self.data) != TRACKS*SECTORSPERTRACK*SECTORSIZE:
            raise Exception("Unexpected size for", filename)
        self.listdir()

    def format(self):
        self.data = bytearray([0xFF]*TRACKS*SECTORSPERTRACK*SECTORSIZE)
        ds = (DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE
        self.data[ds:ds+DIRENTRYNUM *
                  DIRENTRYLEN] = bytes([0x00]*DIRENTRYNUM*DIRENTRYLEN)
        fs = (FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        CLUSTERSPERTRACK = int(SECTORSPERTRACK/SECTORSPERCLUSTER)
        self.data[fs:fs+CLUSTERSPERTRACK] = bytes([0xFE]*CLUSTERSPERTRACK)
        self.data[fs+20*CLUSTERSPERTRACK:fs+21 *
                  CLUSTERSPERTRACK] = bytes([0xFE]*CLUSTERSPERTRACK)
        self.listdir()

    def get(self, track, sector, length=SECTORSIZE):
        start = (track*SECTORSPERTRACK+sector)*SECTORSIZE
        return self.data[start:start+length]

    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(self.data)

    def listdir(self):
        self.files = {}
        dd = self.get(DIRTRACK, DIRSECTOR, DIRENTRYNUM*DIRENTRYLEN)
        for f in range(DIRENTRYNUM):
            i = f*16
            fd = dd[i:i+16]
            if fd[0] != 0x00:
                try:
                    name = fd[:12].decode("utf-8")
                except:
                    name = tuple(fd[:12])
                self.files[name] = [int(x) for x in fd[12:14]]
            # print(fd)

    def getDiskIPL(self):
        return self.get(0, 0)

    def getDiskName(self):
        return self.get(0, 0, 0x20)

    def getCluster(self, cluster, sectors):
        start = cluster*SECTORSPERCLUSTER*SECTORSIZE
        return self.data[start:start+sectors*SECTORSIZE]

    def getChain(self, start):
        f = self.get(FATTRACK, FATSECTOR, 160)
        l = [start]
        while f[start] < 160:
            start = f[start]
            l.append(start)
        return l, f[start] & 0x0F

    def getFreeClusters(self):
        f = self.get(FATTRACK, FATSECTOR, 160)
        return [i for i, v in enumerate(f) if v == 0xFF]

    def getDiskUsage(self):
        f = self.get(FATTRACK, FATSECTOR, 160)
        free = [i for i, v in enumerate(f) if v == 0xFF]
        system = [i for i, v in enumerate(f) if v == 0xFE]
        used = [i for i, v in enumerate(f) if v != 0xFE and v != 0xFF]
        fat = list(range(FATTRACK*CLUSTERSPERTRACK,
                   (FATTRACK+1)*CLUSTERSPERTRACK))
        for i in fat:
            if f[i] != 0xFE:
                print("Fat track not marked as 0xFE")
        system = list(set(system)-set(fat))

        return {"system": system, "fat": fat, "used": used, "free": free}

    def getSystem(self):
        fat = self.get(FATTRACK, FATSECTOR, 160)
        reservedChunks = [[], ]

        for i in range(int(DIRTRACK*SECTORSPERTRACK/SECTORSPERCLUSTER)):
            if fat[i] == 0xFE:
                l = reservedChunks[-1]
                if len(l) > 0 and l[-1] != i-1:
                    reservedChunks.append([])
                reservedChunks[-1].append(i)

        data = []
        print(f"Found {len(reservedChunks)} IPL chunks")
        for chunk in reservedChunks:
            print("Chunk size", (chunk[-1]-chunk[0]+1), "K")
            d = self.getCluster(
                chunk[0], SECTORSPERCLUSTER*(chunk[-1]-chunk[0]+1))
            data.append((chunk[0], d))

        return data

    def addSystem(self, cluster, data):
        start = cluster*SECTORSPERCLUSTER*SECTORSIZE
        self.data[start:start+len(data)] = data
        fs = (FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        csize = math.ceil(len(data) / (SECTORSPERCLUSTER*SECTORSIZE))
        self.data[fs+cluster:fs+cluster+csize] = bytes([0xFE]*csize)
        print("adding system data,", len(data), "bytes",
              "using", csize, "clusters from cluster", cluster)

    def getFile(self, name):
        start, _ = self.files[name]
        if start >= 160:
            print("File start from invalid cluster", start)
            return []
        chain, lastUsage = self.getChain(start)
        fdata = bytearray()
        for c in chain[:-1]:
            fdata += self.getCluster(c, 4)
        fdata += self.getCluster(chain[-1], lastUsage)
        return fdata

    def delSector(self, c):
        fs = (FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        self.data[fs+c] = 0xFF
        secstart = c*SECTORSPERCLUSTER*SECTORSIZE
        secend = (c+1)*SECTORSPERCLUSTER*SECTORSIZE
        self.data[secstart:secend] = bytes([0xFF]*SECTORSPERCLUSTER*SECTORSIZE)

    def delete(self, name):
        start, _ = self.files[name]
        chain, lastUsage = self.getChain(start)
        for c in chain:
            self.delSector(c)
        dd = self.get(DIRTRACK, DIRSECTOR, DIRENTRYNUM*DIRENTRYLEN)
        for f in range(DIRENTRYNUM):
            fd = dd[f*DIRENTRYLEN:(f+1)*DIRENTRYLEN]
            es = (DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE+f*DIRENTRYLEN
            # print("fd",fd,"entry",self.data[es:es+DIRENTRYLEN])
            if fd[:12].decode("utf-8") == name:
                print("Deleting entry", self.data[es:es+DIRENTRYLEN])
                self.data[es:es+DIRENTRYLEN] = bytes([0x00]*DIRENTRYLEN)

    def addFile(self, name, d):
        entry = bytearray([0x00]*DIRENTRYLEN)
        for i in range(12):
            entry[i] = 0x20
        nl = min(len(name), 12)
        entry[:nl] = bytes(name[:nl].encode("utf-8"))

        chain = []
        fs = (FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        n = int(len(d)/(SECTORSPERCLUSTER*SECTORSIZE))
        if n*SECTORSPERCLUSTER*SECTORSIZE < len(d):
            n += 1
        lastUsage = 0xC4 - \
            int((n*SECTORSPERCLUSTER*SECTORSIZE-len(d))/SECTORSIZE)
        c = 0
        while len(chain) < n and c < 160:
            if self.data[fs+c] == 0xFF:
                chain.append(c)
            c += 1
        if len(chain) < n:
            raise Exception("Not enough space to store", filename)

        fp = 0
        SECSIZE = SECTORSPERCLUSTER*SECTORSIZE
        # print("chain",[hex(c) for c in chain],"lu",lastUsage)
        for c, n in zip(chain, chain[1:]+[lastUsage]):
            self.data[fs+c] = n
            secstart = c*SECSIZE
            chunk = d[fp:fp+SECSIZE]
            self.data[secstart:secstart+len(chunk)] = chunk
            fp += SECSIZE

        entry[12] = chain[0]

        ds = (DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE
        entryRec = False
        for f in range(DIRENTRYNUM):
            es = ds+f*DIRENTRYLEN
            if self.data[es] == 0x00:
                self.data[es:es+DIRENTRYLEN] = entry
                print("Added entry", entry)
                entryRec = True
                break
        if not entryRec:
            raise Exception(
                "No more directory entries available for", filename)

    def deleteUserfiles(self):
        f = self.get(FATTRACK, FATSECTOR, 160)
        for idx, val in enumerate(f):
            if val != 0xFE:
                self.delSector(idx)
        ds = (DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE
        self.data[ds:ds+DIRSECLEN*SECTORSIZE] = bytes([0x00]*12*SECTORSIZE)

    def printSummary(self):
        print(self.filename)
        print(self.getDiskName())
        summary = " ".join(
            [f"{n}={len(c)}K" for n, c in self.getDiskUsage().items()])
        print(summary)
        self.listdir()
        for idx, (fname, sc) in enumerate(self.files.items()):
            print(f"{idx+1:2})", fname, len(self.getFile(fname)), "bytes")

    def printFat(self):
        fat = self.get(FATTRACK, FATSECTOR, 160)
        chains = [-1]*160

        for idx, fname in enumerate(self.files):
            start, _ = self.files[fname]
            if start >= 160:
                print("File", fname, "starts from invalid cluster", start)
                continue

            chain, lastUsage = self.getChain(start)
            for c in chain:
                chains[c] = idx+1

        def clusterState(t, c):
            idx = t*CLUSTERSPERTRACK+c
            s = f"[{idx:02x}]{fat[idx]:02x}"
            if chains[t*CLUSTERSPERTRACK+c] >= 0:
                s += f"({chains[idx]:02d})"
            else:
                s += " "*4
            return s

        for t in range(TRACKS):
            status = " ".join(
                [f"{clusterState(t,c)}" for c in range(CLUSTERSPERTRACK)])
            print(f"{t:2d}", status)


def canonicalName(name):
    if "." in name:
        tok = name.split(".")
        n = ".".join(tok[:-1])
        e = tok[-1]
        name = n[:8].ljust(8)+"."+e
    return name


def extract(f, dirname):
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
    for fname in f.files:
        with open(os.path.join(dirname, f"{fname}"), "wb") as of:
            of.write(f.getFile(fname))

    for c, d in f.getSystem():
        with open(os.path.join(dirname, f"IPL{c}"), "wb") as of:
            of.write(d)


def pack(f, dirname):
    for fname in sorted(os.listdir(dirname)):
        if fname[:3] == "IPL":
            d = open(os.path.join(dirname, fname), "rb").read()
            f.addSystem(int(fname[3:]), d)
    for fname in sorted(os.listdir(dirname)):
        if fname[:3] != "IPL":
            d = open(os.path.join(dirname, fname), "rb").read()
            f.addFile(fname, d)


def setSystem(f, fname):
    d = open(fname, "rb").read()
    f.addSystem(0, d)


commands = {
    "help": lambda f: print("Available commands "+" ".join(getLongOptions())),
    "open": lambda f, opt: f.open(opt),
    "save": lambda f, opt: f.save(opt),
    "extract": extract,
    "pack": pack,
    "format": lambda f: f.format(),
    "list": lambda f: f.printSummary(),
    "listfat": lambda f: f.printFat(),
    "setSystem": setSystem
}


def getLongOptions():
    return [c+"=" if len(signature(f).parameters) > 1 else c for (c, f) in commands.items()]


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage", sys.argv[0], "--command1[=args] --command2[=args]")
    else:

        optlist, _ = getopt.getopt(sys.argv[1:], "", getLongOptions())
        f = Floppy()
        for (c, opt) in optlist:
            func = commands[c[2:]]
            if len(opt) > 0:
                func(f, opt)
            else:
                func(f)
