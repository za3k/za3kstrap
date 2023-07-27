import importlib
import socket
import os

HOSTNAME=socket.gethostname()
def locate_package_file(file=None):
    for path in [
        file,
        "/home/zachary/.packages/{}".format(HOSTNAME),
        "/home/zachary/.ingredients/{}/PACKAGES".format(HOSTNAME),
    ]:
        if path and os.path.exists(path):
            return path
    return None
def load_package_file(package_file):
    aur_packages, regular_packages, groups = [], [], []
    with open(package_file) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line == "":
                continue
            if line.startswith("+"):
                aur_packages.append(line[1:])
            elif line.startswith("*"):
                groups.append(line[1:])
            else:
                regular_packages.append(line)
    return sorted(regular_packages), sorted(groups), sorted(aur_packages)
def get_package_file(file=None):
    package_file = locate_package_file(file=file)
    assert package_file is not None, "Package file not found"
    return load_package_file(package_file)

def subcommand(name):
    if name in ["update_config", "test_repro", "update_state", "make_packages", "make_restore"]:
        print("That command is not yet implemented")
        sys.exit(1)
    try:
        return importlib.import_module("sub."+name).main
    except ImportError:
        subcommand("help")(code=1)

