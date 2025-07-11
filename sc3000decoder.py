#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SC3000 Basic Decoder
Reference:
http://www43.tok2.com/home/cmpslv/Sc3000/EnrSCbas.htm
"""
from command_table import CommandTable
from basic_alias_table import basic_alias_table


class UnknownFunctionException(Exception):
    pass


class UnknownCommandException(Exception):
    pass


def read_bas_as_hex_string(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
        return content.hex().upper()


def print_decoded(decoded, pretty_format=True):
    if pretty_format:
        print(decoded["raw"])
        print("Script length: {}".format(len(decoded["raw"])))
        print_format = "({:04d}) {: >5} {}"
    else:
        print_format = "{1} {2}"
    for line in decoded["result"]:
        print(print_format.format(line["byte"], line["line"], line["cmd"]))


def decode_hex_string(hex_string, suppress_error=True, terminator="0000", includeBin=True):
    result = {"raw": hex_string, "result": [], "errors": 0}
    i = 0
    while i < len(hex_string):
        result_i = {"byte": i, "line": "",
                    "cmd": "", "raw": "", "error": False}
        if hex_string[i:i+len(terminator)] == terminator:
            bin_data = hex_string[i+4:]
            if includeBin and len(bin_data) > 0:
                result_i["cmd"] = f"\\bin " + hex_string[i:]
                di = len(hex_string) - i
            else:
                return result
        elif len(hex_string) >= i+14:
            try:
                di, result_i["line"], result_i["cmd"] = decode_one_line(
                    hex_string[i:], suppress_error)
                result_i["raw"] = " ".join(
                    [hex_string[j:j+2] for j in range(i, i+di, 2)])
            except UnknownFunctionException as e:
                print("Error: {}".format(e))
                break
            except UnknownCommandException as e:
                print("Error: {}".format(e))
                break
            except StopIteration:
                print("no data after 0x80")
                break
        else:
            return result
        i += di
        if hex_string[i-2:i] != "0D":
            result_i["error"] = True
            result["errors"] += 1
        result["result"].append(result_i)
    return result


# LEN LINE_L LINE_H 00 00 .... 0D
def decode_one_line(line, suppress_error=True):
    result = ""
    command_length = int(line[0:2], 16)
    di = 10+command_length*2+2
    line_number = int(line[4:6]+line[2:4], 16)
    blank = line[6:10]
    result = decode_command(line[10:di-2], line_number, suppress_error)
    return di, line_number, result


def decode_command(command, line_number, suppress_error=True):
    result = ""
    zipper = zip(command[0::2], command[1::2])
    inside_data = False
    inside_rem = False
    inside_quote = False

    for l, (i, j) in enumerate(zipper):
        current_result = ""
        if i+j < "80" or inside_data or inside_rem or inside_quote:
            current_result = decode_ascii(i+j)
        elif i+j == "80":
            i, j = next(zipper)
            try:
                current_result = CommandTable.FUNCTION[i+j]
            except KeyError:
                msg = "Unknown Function {}{} on line {}".format(
                    i, j, line_number)
                if suppress_error:
                    current_result = "\\f{}{}".format(i, j)
                    print("Warning: " + msg)
                else:
                    raise UnknownFunctionException(msg)
        else:
            try:
                current_result = CommandTable.COMMAND[i+j]
            except KeyError:
                msg = "Unknown Command {}{} on line {}".format(
                    i, j, line_number)
                if suppress_error:
                    current_result = "\\c{}{}".format(i, j)
                    print("Warning: " + msg)
                else:
                    raise UnknownCommandException(msg)

        # Characters between Double quote, or after DATA or REM, should be treated as ascii
        if current_result == "DATA":
            inside_data = True
        elif current_result == "REM":
            inside_rem = True
            # Ignore the rest of the line
            # https://www.c64-wiki.com/wiki/REM
        elif current_result == '"':
            inside_quote = not inside_quote
        elif current_result == ":":
            inside_data = False
        result += current_result

    return result


def escape_char(ch, toPass=[]):
    if ch in toPass or 0x20 <= ch <= 0x7E and ch != "\\":
        return chr(ch)
    return basic_alias_table.decode(ch)


def decode_ascii(byte):
    ch = int(byte, 16)
    return escape_char(ch)


def save_decoded_to(filepath, decoded):
    with open(filepath, "w", encoding="utf-8") as f:
        for line in decoded["result"]:
            f.write("{1} {2}\n".format(
                line["byte"], line["line"], line["cmd"]))
