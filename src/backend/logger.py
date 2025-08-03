"""
Custom logger by me, since I'm not a fan of the standard logging module
"""

# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import os
import json
from enum import Enum
from colorama import just_fix_windows_console

__all__ = ["LoggingLevel", "Logging", "logging", "enable_logging", "disable_logging", "loggingconfig", "loadconfig",
           "writeconfig"]


class LoggingLevel(Enum):
    Debug = 1
    Info = 2
    Important = 3
    SuperImportant = 5
    Warning = 6


class Logging:

    def __init__(self, usedefaults: bool = True, synclog: bool = True, **kwargs) -> None:
        """
        :param usedefaults: Whether to use the default logging settings
        :param synclog: Whether to sync the Log list with other instances of this class
        :param kwargs: If usedefaults is False, supply your own logging settings here:
            colorized=True
            printwarnings=True
            printdebug=False
            printinfo=True
            printimportant=False
            printsuperimportant=True
            printspecial=True
            donotprintspecial=False
            donotprintsuccessinfo=True
            allowoverride=True
            printall=True
            printnone=False
        """
        if usedefaults:
            self._fromoptions(**loadconfig())
        else:
            self._fromoptions(**kwargs)
        if synclog:
            self.Log = _Log
        else:
            self.Log = []
        self.enabled = False if self.printnone else True

    # noinspection IncorrectFormatting
    def _fromoptions(self,
                     colorized=True,
                     printwarnings=True,
                     printdebug=False,
                     printinfo=True,
                     printimportant=False,
                     printsuperimportant=True,
                     printspecial=True,
                     donotprintspecial=False,
                     donotprintsuccessinfo=True,
                     allowoverride=True,
                     printall=True,
                     printnone=False
                     ):
        self.colorized = colorized
        self.printwarnings = printwarnings
        self.printdebug = printdebug
        self.printinfo = printinfo
        self.printimportant = printimportant
        self.printsuperimportant = printsuperimportant
        self.printspecial = printspecial
        self.donotprintspecial = donotprintspecial
        self.donotprintsuccessinfo = donotprintsuccessinfo
        self.allowoverride = allowoverride
        self.printall = printall
        self.printnone = printnone

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def log(self, message: str, level: LoggingLevel = LoggingLevel.Info, override: bool = False,
            successinfo: bool = False, special: bool = False) -> None:
        self.Log.append(message)
        if self.printnone:
            return
        if not (override and self.allowoverride):
            if successinfo and self.donotprintsuccessinfo:
                return
            if special and self.donotprintspecial:
                return
        if self.printall:
            toprint = True
        elif level == LoggingLevel.Debug and self.printdebug:
            toprint = True
        elif level == LoggingLevel.Info and self.printinfo:
            toprint = True
        elif level == LoggingLevel.Important and self.printimportant:
            toprint = True
        elif level == LoggingLevel.SuperImportant and self.printsuperimportant:
            toprint = True
        elif special and self.printspecial:
            toprint = True
        else:
            toprint = False
        if toprint and _enabled and self.enabled:
            self.printmessage(message, level, special, self.colorized)

    def printlog(self):
        print("\n".join(self.Log))

    @staticmethod
    def printmessage(message: str, level: LoggingLevel, special: bool, colorized: bool) -> None:
        colors = {
            "Debug": "\033[0m",
            "Info": "\033[94m",
            "Important": "\033[96m",
            "SuperImportant": "\033[93m",
            "Warning": "\033[91m",
            "Special": "\033[92m",
            "reset": "\033[0m"
        }
        if colorized:
            if special:
                print(f"{colors['Special']}[{level.name}] [Special]: {message}{colors['reset']}")
            else:
                if level.name in colors:
                    print(f"{colors[level.name]}[{level.name}]: {message}{colors['reset']}")
                else:
                    print(f"[{level.name}]: {message}")
        else:
            if special:
                print(f"[{level.name}] [Special]: {message}")
            else:
                print(f"[{level.name}]: {message}")

    def warning(self, message: str, warningtype: BaseException = None, override: bool = False) -> None:
        if warningtype:
            self.Log.append(f"[Warning]: {warningtype}: {message}")
            if override or self.printwarnings and _enabled and self.enabled:
                self.printmessage(f"{warningtype}: {message}", LoggingLevel.Warning, False, self.colorized)
        else:
            self.Log.append(f"[Warning]: {message}")
            if override or self.printwarnings and _enabled and self.enabled:
                self.printmessage(message, LoggingLevel.Warning, False, self.colorized)


def disable_logging() -> None:
    """
    Disables logging to console with print statements
    """
    global _enabled
    _enabled = False


def enable_logging() -> None:
    """
    Enables logging to console with print statements
    """
    global _enabled
    _enabled = True


def loadconfig() -> dict:
    if os.path.exists(configpath):
        with open(configpath, "r") as f:
            return json.load(f)
    else:
        """
        loggingconfig.json does not exist, fall back to hardcoded defaults
        """
        return _defaults


def writeconfig(config: dict) -> None:
    with open(configpath, "w") as f:
        json.dump(config, f, indent=4)


def loggingconfig(**kwargs) -> dict:
    """
    This is a neat trick that lets me generate a dictionary with my config just by calling
    this function with the options as arguments!
    """
    return kwargs

def get_config_path() -> str:
    """Gets the file path for the logging.config file"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_path, "loggingconfig.json")


# noinspection IncorrectFormatting
_defaults = loggingconfig(colorized=True,
                          printwarnings=True,
                          printdebug=False,
                          printinfo=True,
                          printimportant=False,
                          printsuperimportant=True,
                          printspecial=True,
                          donotprintspecial=False,
                          donotprintsuccessinfo=True,
                          allowoverride=True,
                          printall=True,
                          printnone=False
                          )
configpath = get_config_path()
just_fix_windows_console()
_enabled = True

_Log = []
logging = Logging(usedefaults=True)

#if __name__ == "__main__":
#    if not os.path.exists(configpath):
#        try:
#            writeconfig(_defaults)
#            print(f"Created loggingconfig.json at {configpath}")
#        except Exception as e:
#            print(f"Failed to create loggingconfig.json at {configpath}: {e}")
