"""
THIS IS TODO! Fucking buildozer will NOT work, so I've given up on the Android build for now.
"""


from typing import Optional
import os
from tempfile import gettempdir
from shutil import copyfile, copytree
import subprocess
from subprocess import CalledProcessError
import warnings

__all__ = ["build"]

def _install_requirements():
    try:
        import capstone
        import keystone
        import elftools
        import colorama
        import docopt
        import schema
        import buildozer
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError):
        print("Installing requirements...")
        import capstone
        import keystone
        import elftools
        import colorama
        import docopt
        import schema


_install_requirements()
IS_WINDOWS = os.name == "nt"


def force_rmtree(directory):
    """
    Remove a fucking directory. No readonly files, no symlinks, no shutil.rmtree nonsense. Just REMOVE it,
    for God's sake!
    """
    if IS_WINDOWS:
        subprocess.run(['rmdir', '/s', '/q', directory], shell=True)
    else:
        subprocess.run(['rm', '-rf', directory])


def force_copytree(src, dst):
    """
    Copy a directory forcibly, overwriting existing dst. No readonly files, no symlinks, no shutil.copytree nonsense.
    """
    if IS_WINDOWS:
        """ Fuck this. Let's give ChatGPT a try. """
        # Ensure destination exists
        os.makedirs(dst, exist_ok=True)
        # Use robocopy to copy everything, including subdirs, overwrite files
        subprocess.run(["robocopy", src, dst, "/E", "/COPY:DAT",  # copy all file info (permissions, timestamps)
                        "/R:0",  # no retries
                        "/W:0",  # no wait between retries
                        "/NFL",  # no file list
                        "/NDL",  # no directory list
                        "/NJH",  # no job header
                        "/NJS"  # no job summary
                        ], capture_output=True)
    else:
        copytree(src, dst, dirs_exist_ok=True)


def check_command(command, check_wsl) -> bool:
    """ WARNING: If a command does not terminate itself, this function will HANG INDEFINITELY. Use --version or
        a similar argument if simply calling the executable with no arguments causes it to hang.

        Check if a command exists (cross-platform). If check_wsl, the command will be run inside wsl instead of on the
        base machine.

        The command can be just the executable name (e.g. pip) or that executable with arguments (e.g. pip --version).

        Note: This function only exists because shutil.which() does not work with WSL. If not checking in WSL,
        shutil.which() will do just fine (note that for shutil.which(), only supply the executable name - arguments
        are not supported.
    """
    assert IS_WINDOWS or not check_wsl # Cannot run wsl if it's not Windows

    COMMAND_NOT_FOUND: int = 127  # Command not found error code
    if IS_WINDOWS and not check_wsl:
        # On Windows, subprocess.run will raise FileNotFoundError if command does not exist
        try:
            run_command(command, check_wsl, print_command=False, capture_output=True)
        except FileNotFoundError:
            return False
        return True
    else:
        # Linux or WSL; either way it will return status code 127 if command does not exist
        # We cannot use shutil.which() because the command may have arguments
        return run_command(command, check_wsl, print_command=False, capture_output=True).returncode != COMMAND_NOT_FOUND



def run_command(command, use_wsl, print_command=True, capture_output=False, check=False,
                wsl_root=False) -> Optional[subprocess.CompletedProcess]:
    if use_wsl:
        build = "wsl "
        if wsl_root:
            build += "-u root "
        command = build + command
    if print_command:
        print(command)
    if capture_output:
        return subprocess.run(command, shell=True, capture_output=True, check=check)
    else:
        subprocess.run(command, shell=True, check=check)


def check_wsl_installed():
    """Check if WSL is installed on Windows."""
    assert IS_WINDOWS
    # noinspection PyBroadException
    if check_command("wsl --status", False):
        return True
    if check_command("wsl -l", False):
        return True
    return False


def build(debug, save_buildozer_cache=True):
    """
    Build the APK with buildozer. Handles everything. If the original path contains spaces, building will be done in
    a temp directory.

    debug - Whether to build as debug (false for release build)
    save_buildozer_cache - If building is done in a temp directory (because original path contains spaces), whether to
    save the .buildozer folder generated during builds in its own temp directory so it persists across builds. Only
    applies if a temp directory is used for building. This will make builds much faster after the first one. If
    something goes wrong with buildozer, you may have to delete
    this cache.
    """
    print("Note: This will take a while! Let it run while you do something else.")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    using_temp_dir = False
    if " " in root_dir:
        #raise Exception("Buildozer does not support spaces in file paths. Please move the entire"
        #                " Gameguardian-All-Updates-Script-Generator project to a path without spaces and try"
        #                " again.")
        warnings.warn("Buildozer does not support spaces. This script will copy the entire src directory to a temporary"
                      " directory, build the APK, then delete the temp directory."
                      " To prevent this from happening, move the entire Gameguardian-All-Updates-Script-Generator"
                      " project to a path without spaces.")
        using_temp_dir = True
        old_root = root_dir
        root_dir = os.path.join(gettempdir(), "Gameguardian-All-Updates-Script-Generator")
        buildozer_backup_dir = os.path.join(gettempdir(), "Gameguardian-All-Updates-Script-Generator_Buildozer")
        buildozer_cache_dir = os.path.join(root_dir, "src", "Android", ".buildozer")
        print(f"Copying to temp directory {root_dir}")
        force_copytree(os.path.join(old_root, "src"), os.path.join(root_dir, "src"))
        if os.path.exists(buildozer_backup_dir) and save_buildozer_cache:
            # Restore buildozer cache from "persistent" temp
            force_copytree(buildozer_backup_dir, buildozer_cache_dir)
    os.chdir(os.path.join(root_dir, "src/Android"))
    try:
        # noinspection PyPep8Naming
        TEMP_BUILD_DIR = os.path.join(root_dir, "src", "Android", "bin")
        # noinspection PyPep8Naming
        FINAL_BUILD_DIR = os.path.join(root_dir, "dist", "Android")
        """ Check for wsl if on Windows """
        wsl = False
        if IS_WINDOWS:
            if not check_wsl_installed():
                raise Exception("Android build requires Linux to run. Alternatively, install wsl on Windows and try again ("
                                "still run this script from Windows, though - it will automatically detect and use WSL.")
            wsl = True
        """ Detect python executable's name """
        python_executable = None
        PYTHON_NAMES = ("python", "py", "python3", None)
        for python_executable in PYTHON_NAMES:
            if python_executable is None:
                raise Exception("Failed to locate python executable. Please make sure python is installed and"
                                f" added to path{' in wsl' if wsl else ''}.")
            if python_executable == "py" and (wsl or not IS_WINDOWS):
                # The command 'py' only works on Windows.
                # On Linux or WSL, the command py may be installed but will not work (for some weird reason, IDFK).
                # Running py --version will still print something, which will cause a false positive for the
                # check_command function - so we simply skip it.
                continue
            if check_command(f"{python_executable} --version", wsl):
                break
        """ Install buildozer and its dependencies if needed """
        # Make sure /usr/local/bin is in path (this will add it only if it's not already - thanks ChatGPT)
        print("Ensuring /usr/local/bin is in PATH.")
        # noinspection IncorrectFormatting
        run_command(r"""[[ ":$PATH:" != *":/usr/local/bin:"* ]] && export PATH="$PATH:/usr/local/bin" && \
grep -qxF '[[ ":$PATH:" != *":/usr/local/bin:"* ]] && export PATH="$PATH:/usr/local/bin"' ~/.bashrc || \
echo '[[ ":$PATH:" != *":/usr/local/bin:"* ]] && export PATH="$PATH:/usr/local/bin"' >> ~/.bashrc""", wsl,
                    print_command=False, capture_output=True, check=False)
        print("Detecting and installing dependencies...")
        # Pip
        if not check_command("pip --version", wsl):
            # noinspection IncorrectFormatting
            raise Exception("Pip is not installed in wsl. Please install pip in wsl and add it to PATH (run \"wsl sudo"
                            " apt-get install python3-pip\") so the script can install and run buildozer." if wsl else
                            "Pip is not installed. Please install pip and add it to PATH (run \"sudo apt-get install"
                            " pip\") so the script can install and run buildozer.")
        # Buildozer
        if not check_command(f"{python_executable} -m buildozer --version", wsl):
            try:
                run_command("pip install buildozer", wsl, print_command=True, check=True)
                # Sanity check
                run_command(f"{python_executable} -m buildozer --version", wsl, print_command=False,
                            capture_output=True, check=True)
            except CalledProcessError:
                raise Exception("Failed to install buildozer with pip")
        # Cython (force version 0.29.33, as latest version fails)
        result = run_command(f"cython --version", wsl, print_command=False, capture_output=True)
        if not result.returncode == 0 and result.stdout == "Cython version 0.29.33":
            try:
                run_command("pip install cython==0.29.33", wsl, print_command=True, check=True)
                # Cython is installed as command cython3; however, buildozer expects command 'cython'. So, we have to create
                # a command alias to work around this.
                run_command("sudo ln -s /usr/bin/cython3 /usr/local/bin/cython", wsl, print_command=True, check=True,
                            wsl_root=True)
                # Sanity check
                result = run_command(f"cython --version", wsl, print_command=False, capture_output=True)
                assert result.returncode == 0 and result.stdout == "Cython version 0.29.33"
            except (CalledProcessError, AssertionError):
                raise Exception("Failed to install cython==0.29.33 with pip")
        # Javac (and check $JAVA_HOME is set)
        if not check_command(f"javac -version", wsl)\
                or run_command(f"echo $JAVA_HOME", wsl, print_command=False, capture_output=True).stdout == "":
            try:
                # Pyjunus REQUIRES javac version 8. If not version 8, it will fail.
                # TODO: Implement check for version 8.
                run_command("sudo apt install openjdk-8-jdk", wsl, print_command=True, check=True, wsl_root=True)
                run_command("export JAVA_HOME=$(dirname $(dirname readlink -f (which javac)))", wsl,
                            print_command=False, check=True)
                # Sanity check
                run_command(f"javac -version", wsl, print_command=False, capture_output=True, check=True)
                assert run_command(f"echo $JAVA_HOME", wsl, print_command=False, capture_output=True).stdout != ""
            except (CalledProcessError, AssertionError):
                raise Exception("Failed to install javac")
        # Now, make sure java home is in path (this will add it only if it's not already - thanks ChatGPT)
        # noinspection IncorrectFormatting
        run_command(r"""[[ ":$PATH:" != *":$JAVA_HOME/bin:"* ]] && export PATH="$PATH:$JAVA_HOME/bin" && \
grep -qxF '[[ ":$PATH:" != *":$JAVA_HOME/bin:"* ]] && export PATH="$PATH:$JAVA_HOME/bin"' ~/.bashrc || \
echo '[[ ":$PATH:" != *":$JAVA_HOME/bin:"* ]] && export PATH="$PATH:$JAVA_HOME/bin"' >> ~/.bashrc""", wsl,
                    print_command=False, capture_output=True, check=False)
        # Unzip
        if not check_command(f"unzip", wsl):
            try:
                run_command("sudo apt install unzip", wsl, print_command=True, check=True,
                            wsl_root=True)
                # Sanity check
                run_command(f"unzip", wsl, print_command=False, capture_output=True, check=True)
            except CalledProcessError:
                raise Exception("Failed to install unzip")
        # Autoconf
        if not check_command(f"autoconf", wsl):
            try:
                run_command("sudo apt install autoconf automake libtool", wsl, print_command=True, check=True,
                            wsl_root=True)
                # Sanity check
                run_command(f"autoconf", wsl, print_command=False, capture_output=True, check=True)
            except CalledProcessError:
                raise Exception("Failed to install autoconf")
        # Libffi (for ctypes)
        try:
            # If we cannot import _ctypes, we must install libffi
            run_command("python3 -c \"import _ctypes\"", wsl,  print_command=False, capture_output=True, check=True)
        except CalledProcessError:
            try:
                run_command("sudo apt install libffi-dev", wsl, print_command=True, check=True,
                            wsl_root=True)
                # Sanity check
                run_command("python3 -c \"import _ctypes\"", wsl,  print_command=False, capture_output=True, check=True)
            except CalledProcessError:
                raise Exception("Failed to install libffi")
        # libssl
        try:
            run_command("python3 -c \"import ssl; print(ssl.OPENSSL_VERSION)\"", wsl, print_command=True, check=True)
        except CalledProcessError:
            try:
                run_command("sudo apt install libssl-dev openssl-devel", wsl, print_command=True, check=True,
                            wsl_root=True)
                # Sanity check
                run_command("python3 -c \"import ssl; print(ssl.OPENSSL_VERSION)\"", wsl, print_command=True, check=True)
            except CalledProcessError:
                raise Exception("Failed to install autoconf")

        """ Use buildozer to build the APK """
        print("Building APK...")
        if not os.path.exists(os.path.join(os.getcwd(), "buildozer.spec")):
            raise Exception("Failed to locate buildozer.spec - make sure it is next to app.py in the"
                            " src\\Android directory")
        if os.path.exists(TEMP_BUILD_DIR):
            force_rmtree(TEMP_BUILD_DIR)
        try:
            run_command(f"{python_executable} -m buildozer android {'debug' if debug else 'release'}", wsl, check=True)
        except CalledProcessError:
            raise Exception("Failed to build apk with buildozer")
        """ Rename built APK and move to final build destination """
        if not debug:
            # Strip the -release part at the end of APK name (we can keep -debug if it's a debug build)
            for f in os.listdir(TEMP_BUILD_DIR):  # Don't know file name, so we must use os.listdir
                original_name, extension = os.path.splitext(f)
                os.rename(f, f"{original_name.strip('-release-')}{extension}")
        for f in os.listdir(TEMP_BUILD_DIR):  # Don't know file name, so we must use os.listdir
            copyfile(f, FINAL_BUILD_DIR)
    finally:
        if using_temp_dir:
            """
            Shut up PyCharm, these variables are NOT unbound! They are declared if using_temp_dir is declared! Give
            your IDE some brains!
            """
            print(f"Removing temp directory {root_dir}...")
            # noinspection PyUnbounv dLocalVariable
            if os.path.exists(buildozer_cache_dir) and save_buildozer_cache:
                # Copy buildozer cache to "persistent" temp so it can be used for the next build
                # noinspection PyUnboundLocalVariable
                force_copytree(buildozer_cache_dir, buildozer_backup_dir)
            force_rmtree(root_dir)
        # noinspection PyUnboundLocalVariable
        if os.path.exists(TEMP_BUILD_DIR):
            force_rmtree(TEMP_BUILD_DIR)


if __name__ == "__main__":
    build(debug=False)
