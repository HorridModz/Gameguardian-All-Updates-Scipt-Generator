# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Optional
import os
from backend.utils import *

__all__ = ["generate_script"]


def get_script_path(minified: bool) -> str:
    """Gets the file path for the script template"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(__file__))
    if minified:
        return os.path.join(base_path, "resources/minified_script_template.lua")
    else:
        return os.path.join(base_path, "resources/script_template.lua")

def generate_script(search: GroupSearch | SingleValue, architecture: str, libname: str,
                    minified: Optional[bool] = False, max_results: Optional[int] = 30,
                    show_choice_if_too_many_results: Optional[bool] = True, auto_repair: Optional[bool] = True) -> str:
    if auto_repair:
        raise NotImplementedError("Auto Repair has not yet been implemented")
    src_dir = os.path.dirname(os.path.dirname(__file__))
    with open(get_script_path(minified)) as f:
        script = f.read()
    if isinstance(search, SingleValue):
        # noinspection IncorrectFormatting
        script = script.replace("$SINGLE_VALUE$", str(search.value)).replace("$SINGLE_VALUE_TYPE$", search.data_type)\
                       .replace("$OFFSET_FROM_START$", str(search.offset))
        # HACK: We need a semicolon after nil - when minified, it becomes a=nilb=" instead of a=""b=""
        script = script.replace("\"$GROUP_SEARCH$\"", "nil;")
    else:
        # HACK: We need a semicolon after nil - when minified, it becomes a=nilb=" instead of a=""b=""
        script = script.replace("$GROUP_SEARCH$", search.group_search).replace("$OFFSET_FROM_START$",
                                                                               str(search.offset))
        script = script.replace("\"$SINGLE_VALUE$\"", "nil;")
    # noinspection IncorrectFormatting
    script = script.replace("$ARCHITECTURE$", architecture).replace("$LIB_NAME$", libname)\
                   .replace("$MAX_RESULTS$", str(max_results))\
                   .replace("$SHOW_CHOICE_IF_TOO_MANY_RESULTS$", str(show_choice_if_too_many_results).lower())\
                   .replace("$AUTO_REPAIR$", str(auto_repair).lower())
    return script
