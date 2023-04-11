#! /usr/bin/env python3

import glob
import sys
import os
import jsonparse
import audioparse
import bitparse
import basparse
import wavparse
import tzxparse
import basicparse
import seqparse
from section import parseBytesSections, printSummary, listContent, getSections

from util import removeExtension, rhoSweep, rhoSweepMax
import getopt
from pathlib import Path
import hashlib
import json
import traceback

version = "0.01"


# levels are referred to max value, lperiod in seconds
def audioToRemasteredBit(filename, levell, levelh, opts):
    d = audioparse.getRawSection(filename, levell, levelh, opts)
    if "pitch" in opts:
        pitch = float(opts["pitch"])
    else:
        pitch = 1
    d = getSections(d, pitch)
    if len([s for s in d["sections"] if s["type"] == "bytes"]) < 2:
        raise Exception("nothing to parse")

    parseBytesSections(d["sections"], True, "ignore_ff_sections" in opts)
    if len([s for s in d["sections"] if s["type"] == "bytes"]) < 1:
        raise Exception("no meaningful bytes")
    return d


def audioFindBytes(filename, levell, levelh, opts):
    d = audioparse.getRawSection(filename, levell, levelh, opts)
    if "pitch" in opts:
        pitch = float(opts["pitch"])
    else:
        pitch = 1
    d = getSections(d, pitch)
    score = 11*len([s for s in d["sections"] if s["type"] == "bytes"]) / \
        len([s for s in d["sections"] if s["type"] == "level"])
    return score, d


def audioRead(filename, opts):

    deflev = "best" if opts["output_type"] in ["byteseq", "bitseq"] else "auto"

    level = opts.get("level", deflev)

    if level == "best":
        return rhoSweepMax(audioFindBytes, filename, opts)
    elif level == "auto":
        return rhoSweep(audioToRemasteredBit, filename, "auto", opts)
    else:
        lev = float(opts["level"])
        return audioparse.getRawSection(filename, lev, lev, opts)


# def wavRemaster(filename,d):
#     bs=bitparse.toBitRemaster(d)
#     filename="R_"+removeExtension(filename)+".wav"
#     wavparse.writeWav(filename,bs)

# def tzxRemaster(filename,d):
#     bs=bitparse.toBitRemaster(d)
#     filename="R_"+removeExtension(filename)+".tzx"
#     tzxparse.writeTzxFromBs(filename,bs)


def printInfo(filename, d, opt):
    print("INFO", json.dumps(d["info"], sort_keys=True, indent=4))


readers = {
    "mp3": audioRead,
    "wav": audioRead,
    "bit": bitparse.readBit,
    "json": jsonparse.jsonDeserialize,
    "tzx": tzxparse.readTzx,
    "bas": basparse.readBas,
    "basic": basicparse.readBasic,
    "bitseq": seqparse.readByteSeq,
    "byteseq": seqparse.readByteSeq
}

writers = {
    "json": jsonparse.writeJson,
    "bit": lambda f, d, opt: bitparse.writeBit(f, d, True),
    "rawbit": lambda f, d, opt: bitparse.writeBit(f, d, False),
    "bas": basparse.writeBas,
    "wav": wavparse.writeWav,
    "list": lambda f, d, opt: print(f, listContent(d)),
    "summary": lambda f, d, opt: None,
    "tzx": tzxparse.writeTzx,
    "basic": basicparse.writeBasic,
    "bin": basparse.writeBin,
    "info": printInfo,
    "bitseq": seqparse.writeBitSequence,
    "byteseq": seqparse.writeByteSequence
}

remrate = 44100


def getMd5(filename):
    md5_hash = hashlib.md5()
    md5_hash.update(open(filename, "rb").read())
    return md5_hash.hexdigest()


def addSuffix(filename, suff):
    tok = filename.split(".")
    return ".".join(tok[:-1]) + suff + "." + tok[-1]


def to83name(filename, outputtype):
    if len(filename) > 8:

        def charSet(s, e):
            return [chr(x) for x in range(ord(s), ord(e) + 1)]

        cs = charSet("0", "9") + charSet("a", "z") + charSet("A", "Z")
        sf = ""
        for ch in filename:
            if ch in cs:
                sf += ch
        filename = sf

    filename = filename[:8].ljust(8, " ").upper()
    extension = outputtype[:3].ljust(3, " ").upper()
    return filename + "." + extension


def getOutname(filename, outputtype, opts, d):

    if "output_filename_from_content" in opts:
        if "sections" in d:
            for sec in d["sections"]:
                if "Filename" in sec:
                    filename = sec["Filename"]

    suffix = {"none": "", "signal": "", "bit": "_rb", "section": "_rs"}

    suff = suffix[opts["remaster"]]
    if "output_filename" in opts:
        outPath = Path(opts["output_filename"])
    elif "output_filename_8.3" in opts:
        outPath = Path(to83name(filename, outputtype))
    else:
        outPath = Path(removeExtension(filename) + suff + "." + outputtype)
    if "output_dir" in opts:
        outPath = Path(opts["output_dir"]) / str(outPath).strip("/")
    return outPath


def convert(filename, outputtype, opts):
    if outputtype not in writers:
        print("Unknow output type", outputtype)
        print("Known types are", writers.keys())
        raise Exception("Unknown output type ")

    print("specified options", opts)

    inputtype = opts.get("input_type", filename.split(".")[-1].lower())
    opts["output_type"] = outputtype

    if "remaster" not in opts or opts["remaster"] == "auto":
        if inputtype in ["basic", "bas"]:
            remaster = "section"
        elif inputtype in ["bit", "bitseq", "byteseq"]:
            remaster = "bit"
        else:
            remaster = "signal"
    else:
        remaster = opts["remaster"]
        remlevels = ["none", "auto", "signal", "bit", "section"]
        if remaster not in remlevels:
            errmessage = "Unknown remaster level " + \
                remaster+"options are "+" ".join(remlevels)
            raise Exception(errmessage)

    opts["remaster"] = remaster
    if "output_filename_from_content" not in opts:
        outfile = getOutname(filename, outputtype, opts, None)
        if "no_overwrite" in opts and os.path.isfile(outfile):
            print(str(outfile) + " already exists.")
            return

    print("Reading input")
    d = readers[inputtype](filename, opts)

    info = d.setdefault("info", {})

    info.setdefault("source", {
        "filename": Path(filename).name,
        "md5": getMd5(filename)
    })
    tool = info.setdefault("tool", {})
    tool["name"] = "tapeconv"
    tool["version"] = version
    tool["url"] = "https://github.com/fabiodl/sctape"
    tool.setdefault("settings", {})["remaster"] = remaster

    print("Identifying bytes")
    if "pitch" in opts:
        pitch = float(opts["pitch"])
    else:
        pitch = 1

    getSections(d, pitch)
    ignoreSectionErrors = "ignore_section_errors" in opts or (
        outputtype in ["bitseq", "byteseq"] and not "detect_section_errors" in opts)

    ignoreFFsections = "ignore_ff_sections" in opts
    print("Identifying sections")
    parseBytesSections(d["sections"], not ignoreSectionErrors,
                       ignoreFFsections)
    if outputtype != "list":
        printSummary(d, False)

    print("remastering with mode", remaster)
    if remaster == "section":
        print("Remastering sections")
        d["bitrate"] = remrate
        d["signal"] = bitparse.genSignal(d, remrate, True)
    elif remaster == "bit":
        print("Remastering bits")
        d["bitrate"] = remrate
        d["signal"] = bitparse.genSignal(d, remrate, False)
    if "output_filename_from_content" in opts:
        outfile = getOutname(filename, outputtype, opts, d)
    print("Writing output", outfile)
    parent_dir = outfile.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    writers[outputtype](str(outfile), d, opts)


if __name__ == "__main__":
    options = [
        "level=", "pitch=", "mode=", "ignore_section_errors", "detect_section_errors",
        "ignore_ff_sections", "remaster=", "batch", "no_overwrite",
        "output_dir=", "output_filename=", "output_filename_from_content",
        "output_filename_8.3", "input_type=", "program_name=", "program_type=",
        "program_start_addr=", "program_from=", "program_to=", "program_size=",
        "program_rstrip=", "search_precision=", "newline_on="
    ]
    optlist, args = getopt.getopt(sys.argv[1:], "", options)
    if len(args) < 2:
        print("Usage ", sys.argv[0], " inputfile outputtype")
        print("Available options", options)
    else:
        opts = {k[2:]: v for k, v in optlist}

        if "batch" in opts:
            files = [f.strip() for f in open(args[0]).readlines()]
        else:
            if os.path.isfile(args[0]):
                files = [args[0]]
            else:
                files = sorted(glob.glob(args[0]))

            if len(args) >= 1 and len(files) == 0:
                print(f"No such input file[s]: '{args[0]}'", )
        ok = []
        bad = []
        for filename in files:
            try:
                print("converting", filename)
                print("target:", args[1])
                convert(filename, args[1], opts)
                ok.append(filename)
            except Exception as e:
                print(
                    "Impossible to convert", filename, ":", ''.join(
                        traceback.format_exception(None, e, e.__traceback__)))
                bad.append(filename)
            # raise
        if len(ok):
            print("Successfully converted ", ok)
        if len(bad):
            print("Failed converting ", bad)
