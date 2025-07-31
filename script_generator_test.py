import time
from src.backend.utils import *
from src.backend.script_generator import *

libpath = r"C:\Users\zachy\Work\Game Modding\Projects\Pixel Gun 3D\24.4.1\libil2cpp.so"
starttime = time.time()
function_hex = offset_to_hex("offset", libpath)
aob = generate_aob(function_hex, libpath)
search = create_gameguardian_search(aob, libpath)
print(generate_script(search, "64bit", auto_repair=False))
print(f"Done in {time.time() - starttime} seconds.")
