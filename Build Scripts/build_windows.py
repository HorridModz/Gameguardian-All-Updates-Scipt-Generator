import os
import platform
from shutil import copyfile, rmtree, make_archive
import subprocess
import capstone
import keystone


def get_machine_arch():
    if os.environ.get('PROCESSOR_ARCHITEW6432'):
        return 'AMD64'
    return os.environ.get('PROCESSOR_ARCHITECTURE', platform.machine())

if os.name != "nt":
    raise Exception("Your platform is not Windows. To build for Windows, please run this script from a Windows device.")
platform_id = f"Windows-{get_machine_arch()}"
print(f"Detected platform {platform_id}")
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(root_dir, "../src"))

# Build with pyinstaller
if not os.path.exists("../dist/build-temp"):
    os.makedirs("../dist/build-temp")
command = f'pyinstaller Windows/all_updates_generator.py' \
          ' --additional-hooks-dir="../Build Scripts/pyinstaller hooks"' \
          ' --add-data "resources/minified_script_template.lua:resources"' \
          f' --add-data "resources/script_template.lua:resources"' \
          f' --add-binary "{os.path.dirname(keystone.__file__)}:keystone"' \
          f' --add-binary "{os.path.dirname(capstone.__file__)}:capstone"' \
          ' --distpath "../dist/build-temp" --name "all_updates_generator" -y'
print(command)
subprocess.run(command, check=True)
# Add loggingconfig.py file to build directory
copyfile("resources/loggingconfig.json", "../dist/build-temp/all_updates_generator/loggingconfig.json")
# Generate a zip file
make_archive(f"../dist/Windows/Gameguardian All Updates Script Generator {platform_id}", "zip",
             "../dist/build-temp/all_updates_generator")
#rmtree("../dist/build-temp")
