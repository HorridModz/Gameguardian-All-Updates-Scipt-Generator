"""Gameguardian All Updates Script Generator by HorridModz
Generates gameguardian scripts that work on all updates of a game using pattern scanning
https://github.com/HorridModz/Gameguardian-All-Updates-Script-Generator

Usage:
  all_updates_generator -h | --help
  all_updates_generator --simplified_help
  all_updates_generator --version
  all_updates_generator change_logging_level ([--enable | --disable] [--verbose | --disable_verbose]
  [--enable_color | --disable_color] | --reset)
  all_updates_generator generate_group_search <lib_file> (<offset> [--numberofbytes <bytes_num>] | --hex <hex>)
  [--architecture <architecture>][--maxvalues <max_values>] [--prefernooffset]
  all_updates_generator generate_script <lib_file> (<offset> [--numberofbytes <bytes_num>] |--hex <hex>)
  [--architecture <architecture>] <output_path> [--lib_name <lib_name>] [--maxvalues <max_values>]
  [--maxresults <max_results>] [--nochoiceiftoomanyresults] [--minify]

Options:

    -h --help                   Show help.

    --simplified_help           Shows a simplified description of the available commands and how to use them,
                                with examples. Useful for users who are not used to CLI apps or do not understand
                                this tool, and just want to get it up and running.

    --version                   Show version.

    For command change_logging_level:

    --enable                    Re-enable the log (if it has been previously disabled by change_logging_level --disable)
    --verbose                   Enable logging of all debug information (will enable the log if it is currently disabled)
    --disable_verbose           Disable logging of all debug information
    --enable_color              Enable colorized logging (will enable the log if it is currently disabled)
    --disable_color             Disable colorized logging
     --disable                  Disable all logging (except for printing the end results)
     --reset                    Reset logging level to the default (enabled, colorized, and non-verbose)


    For commands generate_group_search and generate_script:
    <lib_file>                  Commands: generate_group_search, generate_script
                                The path to the game's shared object library (.so) file the target function is in.
                                Usually libil2cpp.so for il2cpp games.

    <offset>                    Commands: generate_group_search, generate_script
                                The offset of your target function. Alternatively, you can leave this out and give
                                the function's hex in the game's lib file using the --hex option.

    <output_path>               Commands: generate_script
                                The path to write the generated script to.

    --lib_name <string>         Commands: generate_script
                                Default: Auto-detect
                                Manually specify the name of the shared object library the target function is in
                                (usually libil2cpp.so for il2cpp games). This should match the name of the .so
                                file, unless the file has been renamed. If not given, the lib name will be set to the
                                name of the lib file.

    --architecture <string>     Commands: generate_group_search, generate_script
                                "32bit" or "64bit" | Default: Auto-detect
                                Force the program to use 32bit or 64bit architecture. This is not recommended,
                                as it should automatically detect the architecture from the lib file.


    --numberofbytes <number>    Commands: generate_group_search, generate_script (only for offset, not hex)
                                Positive integer | Default: 1000 | ADVANCED.
                                How many bytes to read when getting hex from lib file and offset (not applicable when
                                hex is supplied instead) - default is 1000. The more bytes that are read past the end of
                                the function (e.g. if numberofbytes is 1000 and the function is 300 bytes), the more
                                dependent the aob will be on adjacent functions (usually methods of the same class or
                                namespace) rather than just the function itself, and the more likely the search is to
                                break when these functions are changed or reordered. Thus, the higher this value is,
                                the more precise the group search may be - but also, the higher the chance of the
                                group search breaking.

    --hex <hex>                 Commands: generate_group_search, generate_script (mutually exclusive with offset)
                                Used to supply the target function's hex in the game's lib file (as opposed to the
                                default, the function offset). Format the hex however you want (as long as there is
                                no non-whitespace byte separator or whitespace interrupting bytes - e.g. 1A 2B is
                                fine, but not 1 A 2 B or 1A | 2B).

    --maxvalues <number>        Commands: generate_group_search, generate_script
                                Integer from 1-64 | Default: 8 | ADVANCED
                                Goal for how many values to put in generated group search, if this many can be found.
                                Increasing this number will make the group search more precise and decrease the odds
                                of getting multiple results, but in turn it will be slower. It is not recommended to
                                change this unless you have a good reason - however, if you are getting too many
                                results and need to decrease the number, increasing this value is the recommended way.
                                The maximum is 64 due to gameguardian's limitations,  though you should never
                                realistically need this many.

    --prefernooffset            Commands: generate_group_search
                                ADVANCED
                                Whether to try to generate a group search which includes the first bytes of the aob.
                                This will make the offset 0 and thus mean that the first result when the group search is
                                performed will be the start of the function, saving you the trouble of having to
                                calculate the function's start address in the gameguardian script. However,
                                it may make the group search slightly less precise. Also, it may fail (if the first
                                bytes of the aob are not static).

    --noautorepair              Commands: generate_script
                                NOTE: AS AUTO REPAIR IS NOT YET IMPLEMENTED, THIS OPTION IS IRRELEVANT. DO NOT USE IT.
                                Disable auto repair, a feature that allows the script to automatically edit and
                                fix itself when the target functon is edited and the group search stops working.

    --maxresults <number>       Commands: generate_script
                                Positive integer OR -1 for no maximum | Default: 30
                                The maximum results (number of functions) permitted in the
                                script when the group search is performed. If more than this many results are found,
                                the generated script will show a warning and ask the user if they want to continue or
                                exit - or, if nochoiceiftoomanyresults is set, exit immediately, as editing too many
                                results may cause (usually harmless) glitches or crashes. Set to -1 to permit any
                                amount of results. Default 30.

    --nochoiceiftoomanyresults  Commands: generate_script
                                If more than maxresults (default 30) results are found, the generated script will by
                                default show a warning and ask the user if they want to continue or exit, as editing
                                too many results may cause (usually harmless) glitches or crashes. If this
                                option is set, the script will take away this choice and instead, immediately
                                terminate when too many results are found. To do the contrary and always continue
                                without a choice, set maxresults to -1.

    --minify                    Commands: generate_script
                                Whether to condense the generated script template so it takes up less space. This
                                will have no effect on the function of the script.
"""

SIMPLIFIED_HELP_MESSAGE = """SIMPLIFIED HELP | Run "all_updates_generator -h" for full help

Gameguardian All Updates Script Generator by HorridModz
Generates gameguardian scripts that work on all updates of a game using pattern scanning
https://github.com/HorridModz/Gameguardian-All-Updates-Script-Generator

Are you struggling to use this tool or unfamiliar with CLIs? No problem! You can check the github repository (linked 
above) for instructions, but here's a quick rundown if you just want to make your script:

To generate a script, run "all_updates_generator generate_script", and add the following arguments:
    - The path to your lib file (libil2cpp.so or other) - put this in quotes
    - EITHER THE OFFSET OF YOUR FUNCTION:
        - function offset (e.g. 0xFC6781)
        - OPTIONAL: --numberofbytes <number> (ADVANCED)- How many bytes to read when getting hex from lib file and 
                                                         offset
      OR THE FUNCTION'S HEX VALUE FROM YOUR LIB:
        - -- hex HEX - hex value obtained from your lib by copying the bytes starting from the function's offset
                       (e.g. F6 CB 10 A9)
    - OPTIONAL: --architecture <string> - the architecture of the game you are modding (should match your lib 
                                              file's architecture), either "32bit" or "64bit".
                                              Leave this out to auto-detect architecture from lib file (recommended)
    - The output path for the generated script - put this in quotes
    - OPTIONAL: --lib_name <string> - The name of your game's lib (should match the name of the lib file, unless the 
                                      file has been renamed). Usually libil2cpp.so for il2cpp games.
                                      Leave this out if the lib name matches your lib file.
    - OPTIONAL: --maxvalues <number> (ADVANCED)
                                             Goal for how many values to put in the generated group search, if
                                             this many can be found. Default 8.
    - OPTIONAL: --noautorepair               NOTE: AS AUTO REPAIR IS NOT YET IMPLEMENTED, THIS OPTION IS IRRELEVANT.
                                             DO NOT USE IT.
                                             Disable auto repair, a feature that allows the script to automatically
                                             edit and fix itself when the target functon is edited and the group search 
                                             stops working.
    - OPTIONAL: --maxresults <number>        Set a limit for how many functions the script will allow, in the event 
                                             that more than one result comes up. If more than this many results are
                                             found, the script will ask the user whether they want to proceed
                                             (potentiallyc ausing a crash) or cancel.
                                             Set to -1 for any number of results. Default 30.
    - OPTIONAL: --nochoiceiftoomanyresults   In the event that more than the maximum allowed number of results
                                             (MAXRESULTS - default 30), terminate the script.
    - OPTIONAL: --minify                     Condense the generated script template so it takes up less space. This
                                             will have no effect on the function of the script.
    
    Example usage:
        -  all_updates_generator generate_script "C:\Desktop\libil2cpp.so" 0xFC6781 "C\Desktop\my_script.lua"
        -  all_updates_generator generate_script "C:\Desktop\libil2cpp.so" --hex 1F B4 09 CD 21 B8 01 4C CD 21 90 90 54
           68 69 73 20 70 72 6F 67 72 61 6D 20 6D 75 73 74 20 62 65 20 72 75 6E 20 75 6E 64 65 72 20 57 69 6E 36 34 0D
           0A 24 37 "C\Desktop\my_script.lua"
        -  all_updates_generator generate_script "C:\Desktop\libil2cpp.so" 0xFC6781 "C\Desktop\my_script.lua"
           --maxvalues 20 --maxresults 30 --nochoiceiftoomanyresults --minify

To generate a group search, run "all_updates_generator generate_group_search", and add the 
following arguments:
    - The path to your lib file (libil2cpp.so or other) - put this in quotes
    - EITHER THE OFFSET OF YOUR FUNCTION:
        - function offset (e.g. 0xFC6781)
        - OPTIONAL: --numberofbytes NUMBER (ADVANCED) - How many bytes to read when getting hex from lib file and offset
      OR THE FUNCTION'S HEX VALUE FROM YOUR LIB:
        - --hex HEX - hex value obtained from your lib by copying a sequence of bytes starting from the function's 
                      offset (e.g. F6 CB 10 A9)
    - OPTIONAL: --architecture ARCHITECTURE - the architecture of the game you are modding (should match your lib 
                                              file's architecture), either "32bit" or "64bit".
                                              Leave this out to auto-detect architecture from lib file (recommended)
    - OPTIONAL: --maxvalues MAXVALUES (ADVANCED) - Goal for how many values to put in the generated group search, 
                                                   if this many can be found. Default 8.
    - OPTIONAL: --prefernooffset (ADVANCED) - Whether to try to generate a group search with offset 0, which will 
                                              make it so the first result when the group search is performed will be the
                                              start of the function.
    
    Example usage:
        -  all_updates_generator generate_group_search "C:\Desktop\libil2cpp.so" 0xFC6781
        -  all_updates_generator generate_group_search "C:\Desktop\libil2cpp.so" --hex 1F B4 09 CD 21 B8 01 4C CD 21 
           90 90 54 68 69 73 20 70 72 6F 67 72 61 6D 20 6D 75 73 74 20 62 65 20 72 75 6E 20 75 6E 64 65 72 20 57 69 6E
           36 34 0D 0A 24 37
        -  all_updates_generator generate_group_search "C:\Desktop\libil2cpp.so" 0xFC6781 --maxvalues 20
           --prefernooffset

To configure logging, run "all_updates_generator change_logging_level", with the option you want:
    
    Re-enable the log (if it has been previously disabled by change_logging_level --disable):
        all_updates_generator change_logging_level --enable
    Enable logging of all debug information (will enable the log if it is currently disabled):
        all_updates_generator change_logging_level --verbose
    Disable logging of all debug information:
        all_updates_generator change_logging_level --disable_verbose
    Enable colorized logging (will enable the log if it is currently disabled):
        all_updates_generator change_logging_level --enable_color
    Disable colorized logging:
        all_updates_generator change_logging_level --disable_color
    Disable all logging (except for printing the end results):
        all_updates_generator change_logging_level --disable
    Reset logging level to the default (enabled, colorized, and non-verbose):
        all_updates_generator change_logging_level --reset
"""


__all__ = ["main"]

# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from docopt import docopt
from schema import Schema, And, Use, Optional, SchemaError
import re
from sys import exit
import backend.logger as logger
from backend.logger import logging, LoggingLevel
from backend.utils import *
from backend.script_generator import *

HEX_BYTE_REGEX = "[a-fA-F0-9]{2}"


def format_hex(hexbytes: str) -> str:
    return " ".join([match.strip() for match in re.findall(f"(?i)(\s*{HEX_BYTE_REGEX}\s*)", hexbytes)]).upper()


def print_result(message: str) -> None:
    if logging.enabled:
        logging.log(message, LoggingLevel.SuperImportant)
    else:
        print(message)

def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 1:
        # No arguments provided - show help
        print(__doc__)
        exit()

    # HACK: For some reason docopt doesn't recognize the --simplified_help flag and errors (displaying usage
    #  instructions and exiting) when I try to run it on "all_updates_generator --simplified_help". So, let's check
    # for the flag before docopt runs.
    if "--simplified_help" in argv:
        print(SIMPLIFIED_HELP_MESSAGE)
        exit()
    args = docopt(__doc__, argv, help=True, version="Gameguardian All Updates Script Generator V1.0")

    # noinspection PyTypeChecker,IncorrectFormatting,PyShadowingNames
    schema = Schema({Optional("<lib_file>"): And(And(os.path.exists, error=f"File {args['<lib_file>']} not found"),
                                                 And(lambda lib_file: os.path.splitext(lib_file)[1] == ".so",
                                                     error="lib_file must be a .so file")),
                     Optional("--lib_name"): Use(lambda lib_name: f"lib{lib_name.lstrip('lib').rstrip('.so')}.so"),
                     Optional("<output_path>"): lambda output_path: open(output_path, "w"),
                     Optional("<offset>"): And( And(lambda offset: int(offset, 16),
                                                    error="offset must be a valid hexadecimal value"),
                                                And(lambda offset: -(1 << 63) <= int(offset, 16) < (1 << 63),
                                                    error="offset is not a valid file offset (out of range)")),
                     Optional("--architecture"): And(Use(lambda architecture: architecture.strip().lower()),
                                                     lambda architecture: architecture in ("32bit", "64bit"),
                                                     error="architecture must be '32bit' or '64bit'"),
                     Optional("--numberofbytes", default=600): And(Use(int, error="numberofbytes must be an integer"),
                                                                   lambda bytes_num: bytes_num > 0,
                                                                   error="numberofbytes must be a positive integer"),
                     Optional("--hex"): And(lambda hexbytes: bytearray.fromhex(hexbytes),
                                            Use(format_hex),
                                            error="hex must be a valid string of hexadecimal bytes"),
                     Optional("--maxvalues", default=8): And(Use(int, error="maxvalues must be an integer"),
                                                             lambda maxvalues: 0 < maxvalues < 64,
                                                             error="maxvalues must be between 1 and 64"),
                     Optional("--maxresults", default=30): And(Use(int, error="maxresults must be an integer"),
                                                               lambda maxresults: maxresults > 0 or maxresults == -1,
                                                               error="maxresults must be a positive integer (or -1 for "
                                                                     "no maximum)")
                     }, ignore_extra_keys=True)
    args_to_validate = {key: value for key, value in args.items() if value is not None}
    try:
        # Since validation may mutate some arguments, we need to update the keys in our original dictionary
        args.update(schema.validate(args_to_validate))
    except SchemaError as e:
        exit(e)
    # Clean up, since this variable is no longer needed
    del args_to_validate

    if args["change_logging_level"]:
        config = logger.loadconfig()
        if args["--disable"]:
            config["printnone"] = True
        elif args["--enable"]:
            config["printnone"] = False
        if args["--verbose"]:
            config["printimportant"] = True
            config["printdebug"] = True
        elif args["--disable_verbose"]:
            config["printimportant"] = False
            config["printdebug"] = False
        if args["--enable_color"]:
            config["colorized"] = True
        elif args["--disable_color"]:
            config["colorized"] = False
        if args["--reset"]:
            # Enabled
            config["printnone"] = False
            # Non-verbose
            config["printinfo"] = False
            config["printdebug"] = False
            # Colorized
            config["colorized"] = True
        logger.writeconfig(config)
        print_result("Successfully changed logging level. This will persist until you change it back.")
        sys.exit()

    if not logging.enabled:
        print("Note: Logging is not enabled. If you would like to re-enable it, run change_logging_level  --enable.")
    lib_file = args["<lib_file>"]
    if args["generate_script"]:
        if args["--lib_name"]:
            lib_name = args["--lib_name"]
        else:
            lib_name = os.path.basename(lib_file)
            logging.log(f"No lib name specified, detected lib name from file: {lib_name}", LoggingLevel.Important)
    if args["--architecture"]:
        architecture = args["--architecture"]
    else:
        logging.log("No architecture specified, using lib file to detect architecture", LoggingLevel.Important)
        architecture = detect_architecture(lib_file)
    if args["<offset>"] is not None:
        try:
            function_hex = offset_to_hex(args["<offset>"], lib_file, args["--numberofbytes"], sep="")
        except Exception as e:
            raise Exception(f"Failed to get function hex at offset {args['<offset>']} in lib file: {e}") from None
    else:
        function_hex = args["--hex"]
    maxvalues = args["--maxvalues"]
    maxresults = args["--maxresults"]
    prefernooffset = args["--prefernooffset"]
    show_choice_if_too_many_results = not args["--nochoiceiftoomanyresults"]
    minify = args["--minify"]

    try:
        aob = generate_aob(function_hex, architecture)
    except Exception as e:
        raise Exception(f"Failed to generate aob for function: {e}") from None
    try:
        search = create_gameguardian_search(aob, lib_file, maxvalues, prefernooffset)
    except Exception as e:
        raise Exception(f"Failed to generate group search: {e}") from None
    if args["generate_group_search"]:
        if isinstance(search, GroupSearch):
            print_result(f"Successfully generated group search:\n{search!r} (Use XA Code App memory region)")
        else:
            if search.occurrences > maxresults and not show_choice_if_too_many_results:
                # Too many occurrences
                raise Exception(f"Failed to generate group search: {e}") from None
            print_result("Failed to generate a group search, but found a single value with very little"
                         f" ({search.occurrences}) occurences:\n{search!r} (Use XA Code App memory region)")
    elif args["generate_script"]:
        output_path = args["<output_path>"]

        with open(output_path, "w") as f:
            f.write(generate_script(search, architecture, lib_name, minify, maxresults,
                                    show_choice_if_too_many_results, auto_repair=False))
            print_result(f"Successfully wrote generated script to file {output_path} - open the file and follow the "
                         "instructions at the top, then it will be ready to go!")


if __name__ == "__main__":
    main()
