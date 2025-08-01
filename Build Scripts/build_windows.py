import os
from shutil import copyfile
import subprocess
import capstone
import keystone

root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(root_dir, "../src"))

# Build with pyinstaller
command = 'pyinstaller Windows/all_updates_generator.py --additional-hooks-dir="../Build Scripts/pyinstaller hooks"' \
          f' --add-data "resources/minified_script_template.lua:resources"' \
          f' --add-data "resources/script_template.lua:resources"' \
          f' --add-binary "{os.path.dirname(keystone.__file__)}:keystone"' \
          f' --add-binary "{os.path.dirname(capstone.__file__)}:capstone"' \
          ' --distpath "../dist/Windows" --name "all_updates_generator" -y'
print(command)
subprocess.run(command)
# Add loggingconfig.py file to build directory
copyfile("resources/loggingconfig.json", "../dist/Windows/all_updates_generator/loggingconfig.json")
