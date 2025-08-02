import sys
import platform
import distro
import os
from shutil import copyfile, rmtree, make_archive
import subprocess
import capstone
import keystone


if sys.platform != "linux" and sys.platform != "linux2":
    raise Exception("Your platform is not linux. To build for Linux, please run this script from a Linux device.")
platform_id = f"{distro.id()}-{distro.version()}-{platform.machine()}"
print(f"Detected platform {platform_id}")
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(root_dir, "../src"))

# Build with pyinstaller
command = f'pyinstaller Linux/all_updates_generator.py' \
          ' --additional-hooks-dir="../Build Scripts/pyinstaller hooks"' \
          ' --add-data "resources/minified_script_template.lua:resources"' \
          f' --add-data "resources/script_template.lua:resources"' \
          f' --add-binary "{os.path.dirname(keystone.__file__)}:keystone"' \
          f' --add-binary "{os.path.dirname(capstone.__file__)}:capstone"' \
          ' --onefile --distpath "../dist/build-temp" --name "all_updates_generator" -y'
print(command)
subprocess.run(command)
# Add loggingconfig.py file to build directory
copyfile("resources/loggingconfig.json", "../dist/Windows/all_updates_generator/loggingconfig.json")
# Generate a zip file
make_archive(f"../dist/Linux/Gameguardian All Updates Script Generator {platform_id}", "zip",
             "../dist/build-temp/all_updates_generator")
#rmtree("../dist/build-temp")
