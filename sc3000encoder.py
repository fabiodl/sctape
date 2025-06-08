#!/usr/bin/env python
# -*- coding: utf-8 -*-

import binascii

from command_table import CommandTable
from basic_alias_table import basic_alias_table


def encode_script_string(script_string, suppress_error=False):
    result = []
    for line in script_string.split("\n"):
        if not line:
            continue
        result.append({"raw": line, "encoded": encode_one_line(line)})
    return result


def encode_one_line(line):
    try:
        line_number, command = line.split(" ", 1)
        encoded_line_number = encode_line_number(line_number)
        encoded_command = encode_command(command)
        encoded_command_length = encode_command_length(encoded_command)
        encoded = (encoded_command_length + encoded_line_number +
                   "0000" + encoded_command + "0D").upper()
        return encoded

    except Exception as e:
        tok = line.split()
        if len(tok) == 2:
            line_number, command = tok
            print("LINE NUMBER IS", line_number)
            if line_number == "\\bin":
                return command

        print(f"unable to convert LINE '{line}'")
        raise e


def encode_line_number(line_number):
    hex_number = f"{int(line_number):04x}"
    return hex_number[2:4]+hex_number[0:2]


def encode_command(command):
    result = ""
    ascii_mode = False
    in_comment = False
    in_quotes = False
    c = 0
    while c < len(command):
        parsed = ""
        if not ascii_mode:
            result_c, parsed, dc = match_one_keyword(command[c:])
        if ascii_mode or not parsed:
            result_c, parsed, dc = encode_one_ascii(command[c:])
        if parsed == '"':
            in_quotes = not in_quotes
        elif parsed in ['REM', 'DATA']:
            in_comment = True
        ascii_mode = in_comment or in_quotes
        c += dc
        result += result_c
    return result


def match_one_keyword(command):
    matching_commands = list(
        filter(lambda cmd: command.startswith(cmd), CommandTable.COMMAND_BY_WORD.keys()))
    matching_functions = list(
        filter(lambda cmd: command.startswith(cmd), CommandTable.FUNCTION_BY_WORD.keys()))
    if matching_commands:
        result = max(matching_commands, key=len)
        return CommandTable.COMMAND_BY_WORD[result], result, len(result)
    elif matching_functions:
        result = max(matching_functions, key=len)
        return "80"+CommandTable.FUNCTION_BY_WORD[result], result, len(result)
    else:
        return "", "", 0


def encode_one_ascii(command):
    r = basic_alias_table.encode(command)
    return r


def encode_command_length(encoded_command):
    return f"{int(len(encoded_command)/2):02x}"


def print_encoded(encoded, pretty_format=False):
    result = ""
    for line in encoded:
        if pretty_format:
            result += "{}\n  {}\n".format(line["raw"], line["encoded"])
        else:
            result += line["encoded"]
    print(result)


def save_encoded_to(filepath, encoded):
    with open(filepath, "wb") as f:
        result = ""
        for line in encoded:
            result += line["encoded"]
        resultb = binascii.a2b_hex(result)
        f.write(resultb)
