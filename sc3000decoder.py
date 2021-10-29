#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SC3000 Basic Decoder
Reference:
http://www43.tok2.com/home/cmpslv/Sc3000/EnrSCbas.htm
"""

from command_table import COMMAND, FUNCTION

END_LOOP_I = 1000000000

class UnknownFunctionException(Exception):
    pass

class UnknownCommandException(Exception):
    pass

def read_bas_as_hex_string(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
        return content.hex().upper()

def print_decoded(decoded, pretty_format = True):
    if pretty_format:
        print(decoded["raw"])
        print("Script length: {}".format(len(decoded["raw"])))
        print_format = "({:04d}) {: >5} {}"
    else:
        print_format = "{1} {2}"
    for line in decoded["result"]:
        print(print_format.format(line["byte"], line["line"], line["cmd"]))

def decode_hex_string(hex_string, suppress_error=False):
    result = {"raw":hex_string, "result":[]}
    i = 0
    MIN_COMMAND_LENGTH = 14
    while i < len(hex_string)-MIN_COMMAND_LENGTH:
        result_i = {"byte":i, "line":"", "cmd":""}
        if hex_string[i:i+4] == "0000":
            result_i["cmd"] = "End of script, remaining hex is {}".format(hex_string[i:])
            di = len(hex_string) - i
        else:
            di, result_i["line"], result_i["cmd"] = decode_one_line(hex_string[i:], suppress_error)
        i += di
        result["result"].append(result_i)
    return result

def decode_one_line(line, suppress_error=False):
    result = ""
    command_length = int(line[0:2],16)
    di = 10+command_length*2+2
    line_number =  int(line[4:6]+line[2:4],16)
    blank = line[6:10]
    try:
        result = decode_command(line[10:di-2])
    except (UnknownFunctionException, UnknownCommandException) as e:
        result = "Error in decoding: {} -- {}".format(e, line[:di-2])
        di = di if suppress_error else END_LOOP_I
    except Exception as e:
        result = "Unknown error while decoding {} -- {}".format(e, line[:di-2])
        di = di if suppress_error else END_LOOP_I
    return di, line_number, result

def decode_command(command):
    result = ""
    zipper = zip(command[0::2], command[1::2])
    force_ascii = False
    inside_quote = False

    for l, (i,j) in enumerate(zipper):
        current_result = ""
        if i+j < "80" or force_ascii or inside_quote:
            current_result = decode_ascii(i+j)
        elif i+j == "80":
            i,j = next(zipper)
            try: current_result = FUNCTION[i+j]
            except KeyError: raise UnknownFunctionException("Unknown function {}".format(i+j))
        else:
            try: current_result = COMMAND[i+j]
            except KeyError: raise UnknownCommandException("Unknown command {}".format(i+j))

        # Characters between Double quote, or after DATA or REM, should be treated as ascii
        if current_result in ["DATA","REM"]:
            # Ignore the rest of the line
            # https://www.c64-wiki.com/wiki/REM
            force_ascii = True
        if current_result == '"':
            inside_quote = not inside_quote

        result += current_result

    return result

def decode_ascii(byte):
    try:
        return bytearray.fromhex(byte).decode()
    except UnicodeDecodeError:
        return "\\x{}".format(byte)

def save_decoded_to(filepath, decoded):
    with open(filepath, "w") as f:
        for line in decoded["result"]:
            f.write("{1} {2}\n".format(line["byte"], line["line"], line["cmd"]))
