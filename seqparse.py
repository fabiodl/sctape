import pathlib
from section import SectionList
from util import lre
import bitparse


def getBitSequence(d):
    if "signal" not in d:
        print("No signal analysis")
        return
    sl = SectionList()
    period = d["bitrate"]*1/1200
    pairs = list(lre(d["signal"]))
    ones = 0
    bits = ""
    for v, l in pairs:
        if v == 1:
            # print(l, period, l < 3.0/16*period)
            if l < 3.0/8*period:
                ones += 1
                if ones == 2:
                    bits += "1"
                    # print("1", end="")
                    ones = 0
            else:
                bits += "0"
                # print("0", end="")
                ones = 0
    return bits


def isByte(x):
    if len(x) < 11:
        return
    if x[0] == "0" and x[9] == "1" and x[10] == "1":
        n = 0
        for d in range(8):
            c = x[1+d]
            if c == "1":
                n += (1 << d)
            elif c == "0":
                pass
            else:
                return None
        return n


def splitBits(data):
    out = ""
    splits = [i for i in range(2, len(data)) if data[i-2:i+1] == "110"]
    if len(splits) == 0:
        return out
    # print(splits)
    out += data[0:splits[0]]+" "
    w = 0
    r = 0
    for i, j in zip(splits, splits[1:]):
        l = j-i
        if w >= 11:
            r += 1
            if r == 8:
                r = 0
                out += "\n"
            out += " "

            w = 0
        out += data[i:j]
        w += l
    if j < len(data):
        out += " "+data[j:]
    return out


def toByte(s):
    if len(s) > 11:
        idx = len(s)-1
        while idx > 0 and s[idx] == "1":
            idx -= 1

        head = s[:idx+2]
        core = s[idx+2:]
        if len(core) >= 11:
            return f"{head} h{len(core)}"

    if len(s) != 11 or s[0] != '0' or s[-2:] != "11":
        print(f"invalid [{s}]")
        return
    n = 0
    for i, ch in enumerate(s[1:-2]):
        if ch == "1":
            n += 1 << i
        elif ch != "0":
            raise Exception("Unknown chunck", s)
    return f"{n:02X}"


def isHex(x):
    try:
        int(x, 16)
        return True
    except:
        return False


def packBytes(data, hexPassthrough=False):
    count = 0
    out = ""
    for chunk in data.split():
        if hexPassthrough and len(chunk.strip()) == 2 and isHex(chunk):
            ab = chunk
        else:
            ab = toByte(chunk)

        if ab:
            out += ab
        else:
            if len(chunk.strip()) == 2:
                chunk = "["+chunk.strip()+"]"
            out += chunk
        out += " "
    return out


def alignBytes(data, newline_on):
    out = ""
    count = 0
    for tok in data.split():
        tok = tok.strip()
        if len(tok) == 0:
            continue
        out += tok
        count += 1
        if len(tok) > 2 and "error" in newline_on or tok == "0D" and "0D" in newline_on or count == 16 and "count" in newline_on or "all" in newline_on:
            out += "\n"
            count = 0
        else:
            out += " "
    return out


def writeBitSequence(fname, d, opts):
    with open(fname, "w") as g:
        g.write(getBitSequence(d))


def writeByteSequence(fname, d, opts):
    newline_on = opts.get("newline_on", "all")
    out = alignBytes(
        packBytes(splitBits(getBitSequence(d))), newline_on)
    if "split_on_header" in opts:
        path = pathlib.Path(fname)
        chunks = [c for c in out.split("h") if c != ""]
        for i, chunk in enumerate(chunks):
            ofname = path.parent/f"{path.stem}{i:02d}{path.suffix}"
            print("chunk as", ofname)
            with open(ofname, "w") as g:
                g.write("h"+chunk)

    else:
        with open(fname, "w") as g:
            out = alignBytes(
                packBytes(splitBits(getBitSequence(d))), newline_on)
            g.write(out)


def seqToBit(data):
    out = ""
    firstHeader = True
    for w in data.split():
        w = w.strip()
        if len(w) == 2:
            w = bitparse.encodeByte(int(w, 16))
        if w == "H":
            if firstHeader:
                firstHeader = False
            else:
                out += " "*1200
            out += "1"*3600
        elif w == "nospace_H":
            out += "1"*3600
        else:
            out += w
    return out


def readByteSeq(filename, opts):
    return bitparse.getSections(seqToBit(open(filename).read()), "ignore_section_errors" in opts)
