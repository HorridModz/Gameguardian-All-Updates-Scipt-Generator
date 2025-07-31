__all__ = ["ArmHexError", "LibDetectionError", "offset_to_hex", "detect_architecture", "generate_aob",
           "create_gameguardian_search", "GroupSearch", "SingleValue"]


# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Optional, Any
from dataclasses import dataclass
from functools import cache
import binascii
from elftools.elf.elffile import ELFFile
import keystone  # keystone-engine
import capstone
from backend.logger import logging, LoggingLevel

if not hasattr(keystone, "Ks"):
    raise ModuleNotFoundError("Wrong keystone module: You have keystone-engine installed, not keystone. You must"
                              " uninstall keystone-engine and install keystone instead.")

HEXTODECIMALTYPES: dict[str, int] = {"Qword": 8, "Dword": 4, "Word": 2, "Byte": 1}


class ArmHexError(Exception):
    """
    Raised when keystone / capstone fails to assembly / disassemble due to a bad input
    """
    pass


class LibDetectionError(Exception):
    """
    Raised when the program fails to detect the architecture (32bit or 64bit) of a lib file
    """
    pass


@cache
def remove_whitespace(s: str) -> str:
    return "".join(s.split())


# Do not cache - https://stackoverflow.com/questions/54909357/how-to-get-functools-lru-cache-to-return-new-instances
def wraptext(s: str, size: int) -> list[str]:
    # Thanks to https://stackoverflow.com/questions/9475241/split-string-every-nth-character
    return [s[i:i + size] for i in range(0, len(s), size)]


# Do not cache - https://stackoverflow.com/questions/54909357/how-to-get-functools-lru-cache-to-return-new-instances
def getbytes(hexstring: str) -> list[str]:
    """
    Splits a hex string into a list of bytes. Convenient function because it accounts for both
    whitespace-separated and un-separated hex strings.
    """
    hexstring = remove_whitespace(hexstring)
    assert len(hexstring) % 2 == 0, "Invalid hex string (odd length)"
    return wraptext(hexstring, 2)


@cache
def bytecount(hexstring: str) -> int:
    """
    Counts the number of bytes in a hex string. Very simple function, but improves readability.
    """
    return len(getbytes(hexstring))


@cache
def tobigendian(hexstr: str) -> str:
    """
    Converts a little endian hex to big endian (and vice versa, though this function is just here to do the former)
    Taken from
    https://www.reddit.com/r/learnpython/comments/w4pql0/comment/ih3hiw3/?utm_source=share&utm_medium=web2x&context=3
    """
    ba = bytearray.fromhex(hexstr)
    ba.reverse()
    return ba.hex()


def offset_to_hex(offset: str, libfile: str, hexbytes: int = 600, sep: str = " "):
    try:
        decimal_offset = int(offset, 16)
    except ValueError:
        raise ValueError(f"Invalid offset: {offset}. Please provide a hexadecimal value.")
    with open(libfile, "rb") as lib:
        # Read certain number of bytes from offset
        lib.seek(decimal_offset)
        hexstr = lib.read(hexbytes).hex().upper()
        if hexstr == "":
            raise Exception(f"Offset {offset} not found in file {libfile}")
        logging.log(f"Got hex value at offset {offset} in lib file {libfile} (reading {hexbytes} bytes):"
                    f"\n{hexstr}", LoggingLevel.Debug, successinfo=True)
        return sep.join(getbytes(hexstr))


@cache
def detect_architecture(libfilepath: str) -> str:
    """
    Detects the architecture (32bit or 64bit) of a lib file
    Uses pyelftools (https://github.com/eliben/pyelftools)

    @param libfilepath: Path to the lib file
    @return: Architecture of the lib file: "32bit" (ARM) or "64bit" (AARCH64). Raises an exception if it is neither.

    :raises LibDetectionError: When it fails to determine the architecture of the file, or when detection succeeds but
                               it is neither ARM nor AARCH64
    """
    try:
        with open(libfilepath, 'rb') as f:
            elffile = ELFFile(f)
    except Exception:
        raise LibDetectionError("Failed to determine architecture of lib file (error occurred with pyelftools). Is it"
                                " a valid ARM or ARM64 .so file?")
    architecture = elffile.get_machine_arch()
    architecture_conversion = {"ARM": "32bit", "AArch64": "64bit"}
    if architecture in architecture_conversion:
        logging.log(f"Detected architecture of lib file: {architecture_conversion[architecture]}",
                    level=LoggingLevel.Important, successinfo=True)
        return architecture_conversion[architecture]
    else:
        raise LibDetectionError(f"Invalid lib file: This file is of {architecture} architecture"
                                " (according to pyelftools), but it must be ARM or ARM64")


@cache
def make_ks(architecture: str) -> keystone.Ks:
    """
    Only do this once, because it is expensive.
    """
    if architecture == "32bit":
        return keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)
    elif architecture == "64bit":
        return keystone.Ks(keystone.KS_ARCH_ARM64, keystone.KS_MODE_LITTLE_ENDIAN)
    else:
        raise ValueError(f"Unrecognized architecture: {architecture}. Only '32bit' and '64bit' are valid strings")


@cache
def make_cs(architecture: str) -> capstone.Cs:
    """
    Only do this once, because it is expensive.
    """
    if architecture == "32bit":
        return capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    elif architecture == "64bit":
        return capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_LITTLE_ENDIAN)
    else:
        raise ValueError(f"Unrecognized architecture: {architecture}. Only '32bit' and '64bit' are valid strings")


@cache
def armtohex(armcode: str, architecture: str, sep: str = " ", upper: bool = True) -> str:
    ks = make_ks(architecture)
    # Convert string of code to list of instructions (split by newline)
    lines = armcode.split("\n")
    convertedhexlist = []
    for instruction in lines:
        if instruction.isspace():
            continue
        try:
            convertedinstruction = ks.asm(instruction, as_bytes=True)[0]
            convertedhexlist.append(binascii.hexlify(convertedinstruction).decode())
        except Exception:
            raise ArmHexError(f"Failed to assemble ARM opcode: {instruction} with {architecture} "
                              f"architecture. Is the ARM instruction valid? Is the architecture correct?") from None
    convertedhex = sep.join(convertedhexlist)
    if upper:
        convertedhex = convertedhex.upper()
    logging.log(
        f"Converted arm code:\n" + "\n".join(lines) + f"\nto hex with {architecture} architecture:\n" + convertedhex,
        LoggingLevel.Debug, successinfo=True)
    return convertedhex


@cache
def hextoarm(hexstr: str, architecture: str) -> list[str]:
    cs = make_cs(architecture)
    convertedinstructions = []
    # Convert hex string to list of hex instructions
    hexinstructions = wraptext(remove_whitespace(hexstr), 8)
    for hexinstruction in hexinstructions:
        try:
            disasm = next(cs.disasm_lite(bytearray.fromhex(hexinstruction), 0x0))
            convertedinstructions.append(" ".join(disasm[2:]))
        except Exception:
            raise ArmHexError(f"Failed to disassemble hex instruction: {hexinstruction} with {architecture}"
                              f" architecture. Check that the hex instruction comes from the right lib file at the "
                              f"right offset, and the architecture is correct.") from None
    # noinspection IncorrectFormatting
    logging.log("Converted hex:\n" + " ".join(
        hexinstructions) + f"\nto arm code with {architecture} architecture:\n" + "\n".join(convertedinstructions),
                LoggingLevel.Debug, successinfo=True)
    return convertedinstructions


def generate_aob(hexbytes: str, architecture: str, wildcard: str = "??", sep: str = " ", upper: bool = True) -> str:
    # Thanks to https://platinmods.com/threads/pattern-search-yet-another-way-to-automatically-find-an-address.140821/
    # for the tutorial I referenced!
    instructions = hextoarm(hexbytes, architecture)
    hexlist = []
    for instruction in instructions:
        if instruction == "" or instruction.isspace():
            continue
        if "0x" in instruction or "#" in instruction:
            hexlist.append(wildcard * 4)
        else:
            hexlist.append(armtohex(instruction, architecture, sep, upper))
    aob = sep.join(hexlist)
    logging.log(f"Generated aob from hex:\n{aob}", LoggingLevel.Info, successinfo=True)
    return aob


def getstaticbytes(hexlist: list[str], sep: str = "", upper: bool = True) -> str:
    """
    NOT USED, DEPRECATED

    Naive approach to aob generation - dumbly compares multiple hex strings and generates an aob by finding bytes that
    are the same throughout. This function is not used, because the generateaobfromhex() function works with only one
    hex and is much smarter and more efficient.
    """
    byteslists = [getbytes(hexstr) for hexstr in hexlist]
    foundbytes = []
    # Zip will stop at length of the shortest byte list, which is what we want
    for bytesatindex in zip(*byteslists):
        if all([bytesatindex[0] == byte for byte in bytesatindex]):
            # All bytes are the same - this byte should be static
            foundbytes.append(bytesatindex[0])
        else:
            # Bytes are not all the same - must not be static
            foundbytes.append("??")
    aob = sep.join(foundbytes)
    if upper:
        aob = aob.upper()
    logging.log(f"Generated aob from hexes with brute force comparison:\n{aob}", LoggingLevel.Info,
                successinfo=True)
    return aob


@cache
def getdecimalvaluesfromhex(hexbytes: str, valuetypes: Optional[list[str]] = None) -> list[dict[str, str | int]]:
    if valuetypes is None:
        # Default to all types
        valuetypes = list(HEXTODECIMALTYPES.keys())  # Capitalize to make it not case-sensitive
    valuetypes = [type_.capitalize() for type_ in valuetypes]
    # Check for unrecognized types
    if not all([type_ in HEXTODECIMALTYPES for type_ in valuetypes]):
        raise ValueError(f"Unrecognized value type: {[type_ not in HEXTODECIMALTYPES for type_ in valuetypes][0]}")

    values = []
    offset = 0
    byteslist = getbytes(hexbytes)
    # Iterate over hextodecimaltypes, starting with the type of the highest length and going down to the lowest length
    # (Qword to Byte)
    for decimaltype, typelength in sorted(HEXTODECIMALTYPES.items(), key=lambda item: item[1], reverse=True):
        while len(byteslist) >= typelength:
            hexsegment = "".join(byteslist[:typelength])
            values.append(
                {"Hex": hexsegment, "Value": int(tobigendian(hexsegment), 16), "Type": decimaltype, "Offset": offset})
            del byteslist[:typelength]
            offset += typelength
    return values


def getdecimalvaluesfromaob(aob: str, valuetypes: Optional[list[str]] = None) -> list[dict[str, Any]]:
    values = []
    builder = ""
    aobbytes = getbytes(aob)
    for offset, byte in enumerate(aobbytes):
        if byte != "??":
            builder += byte
        if byte == "??" or offset == len(aobbytes) - 1:
            if offset == len(aobbytes) - 1:
                # HACK: After hours of banging my head against the wall over multiple days, I have no idea why this
                #  adjustment is necessary. I just can't figure it out. But this fixes it...
                offset += 1
            # Either hex string has ended (hit a dynamic byte), or we have reached the end of the aob
            if builder:
                for value in getdecimalvaluesfromhex(builder, valuetypes):
                    if value["Hex"] in [other_value["Hex"] for other_value in values]:
                        # Duplicate value
                        continue
                    # Calculate absolute offset from start of aob - add the composite hex's offset from start of aob to
                    # the offset of value from beginning of composite hex - the latter is the offset provided by
                    # getdecimalvaluesfromhex().
                    value["Offset"] = offset - bytecount(builder) + value["Offset"]
                    assert aobbytes[value["Offset"]:value["Offset"] + HEXTODECIMALTYPES[value["Type"]]] == getbytes(
                            value["Hex"]), "Internal bug - offset calculation failed"
                    values.append(value)
                builder = ""
    logging.log(f"Got list of decimal values from aob:\n" + "\n".join([str(value) for value in values]),
                LoggingLevel.Debug, successinfo=True)
    return values


@cache
def count_occurrences_in_lib(hexbytes: str, lib_bytes: str) -> int:
    """Lib_bytes should be the contents of the file returned by file.read("rb"), not the file object or path to it"""
    # noinspection PyTypeChecker
    return lib_bytes.count(bytes.fromhex(hexbytes))


def getgroupsearchrange(values: list[dict[str, Any]]) -> int:
    """
    Gets the group search's group size (range of values).
    """
    offsets = [value["Offset"] for value in values]
    searchrange = min(offsets) + max(offsets) + 1
    logging.log(f"Calculated group search range: {searchrange}", LoggingLevel.Info)
    return searchrange


def getoffsetfrombeginning(values: list[dict[str, Any]]) -> int:
    """
    Gets group search offset from beginning of aob. When gameguardian group search is performed, the values will appear
    in order of address - so the first value will be the one with the smallest offset.
    """
    offsets = [value["Offset"] for value in values]
    logging.log(f"Calculated group search offset: {min(offsets)}", LoggingLevel.Info)
    return min(offsets)


@dataclass
class GroupSearch:
    group_search: str
    offset: int

    def __repr__(self):
        return f"{self.group_search} (offset from start = {self.offset})"


@dataclass
class SingleValue:
    value: int
    data_type: str
    occurrences: int
    offset: int

    def __repr__(self):
        return f"{self.value} {self.data_type} (offset from start = {self.offset}) - {self.occurrences} occurrences"


def create_gameguardian_search(aob: Optional[str], libfile: Optional[str], maxvalues: Optional[int] = 8,
                               prefernooffset: Optional[bool] = False,
                               single_value_max_occurrences: Optional[int] = 40) -> GroupSearch | SingleValue:
    if maxvalues < 1:
        raise ValueError("Maxvalues cannot be less than 1")
    if maxvalues > 64:
        raise ValueError("Maxvalues cannot be greater than 64 (due to gameguardian's limitations)")
    logging.log(f"Generating gameguardian group search from aob - max values: {maxvalues}" + (
        " (trying to make group search with 0 offset" if prefernooffset else ""), LoggingLevel.Info)
    with open(libfile, "rb") as f:
        lib = f.read()
    values = getdecimalvaluesfromaob(aob)
    for value in values:
        value["Occurrences"] = count_occurrences_in_lib(value["Hex"], lib)
        if value["Occurrences"] == 0:
            raise Exception("Detected a faulty value that was generated but not found in the lib file."
                            " Check that the hex value or aob is from the correct lib file. If an aob was used, "
                            " it may be outdated.")
    if maxvalues == 1 or len(values) == 1 and values[0]["Occurrences"] <= single_value_max_occurrences:
        # If we have one value but it doesn't have many occurrences, we'll still use it and just generate a value
        # instead of a group search.
        value = values[0]
        # noinspection IncorrectFormatting
        logging.log(f"Failed to generate group search, but found single value with only {value['Occurrences']}:"
                    f"\n{value['Type']} {value['Value']}, Offset: {value['Offset']}",
                    LoggingLevel.Important, successinfo=True)
        if maxvalues == 1:
            logging.warning("This happened because you used \"--maxvalues 1\". Increase this value if you want a more"
                            " precise group search")
        return SingleValue(value["Value"], str(value["Type"]), value['Occurrences'], value["Offset"])
    elif len(values) < 1:
        raise Exception("Failed to make group search - could not find enough static bytes to make a group search")
    # Find top values - sort values by least occurrences and take the first ones
    # noinspection PyShadowingNames
    bestvalues = sorted(values, key=lambda value: value["Occurrences"])[:maxvalues]
    # If we prefer a group search with no offset (offset 0) over the best possible group search, then replace the
    # worst (last) value in the search with the value that has offset 0 (if it exists)
    # noinspection PyShadowingNames
    lowestoffsetvalue = sorted(values, key=lambda value: value["Offset"])[0]
    if prefernooffset:
        if lowestoffsetvalue["Offset"] == 0 and lowestoffsetvalue not in bestvalues:
            bestvalues.pop(-1)
            bestvalues.insert(0, lowestoffsetvalue)
        else:
            logging.warning("Could not generate a group search with an offset of 0")
    # Now sort them by offset, so we can do an ordered group search
    bestvalues = sorted(bestvalues, key=lambda value: value["Offset"])
    logging.log("Found values for group search:\n" + ", ".join(
        f"{value['Value']}{value['Type'][0]}" for value in bestvalues), LoggingLevel.Info)
    groupsearch = ";".join(
        [f"{value['Value']}{value['Type'][0]}" for value in bestvalues]) + f"::{getgroupsearchrange(bestvalues)}"
    offset = getoffsetfrombeginning(bestvalues)
    logging.log(f"Generated group search:\n{groupsearch}\nOffset: {offset}", LoggingLevel.Important)
    return GroupSearch(groupsearch, offset)
