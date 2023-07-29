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
    assert package_file is not None, "PACKAGES file not found"
    return load_package_file(package_file)

def locate_dir_file(file=None):
    for path in [
        file,
        "/home/zachary/.ingredients/{}/DIRS".format(HOSTNAME),
    ]:
        if path and os.path.exists(path):
            return path
def load_dir_file(dir_file):
    lines = []
    with open(dir_file) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line == "": continue
            cat, path = line.split()
            lines.append((cat, path))
        return lines
def get_dir_file(file=None):
    dir_file = locate_dir_file(file=file)
    assert dir_file is not None, "DIRS file not found"
    return load_dir_file(dir_file)

def locate_config_dir(file=None):
    for path in [
        file,
        "/home/zachary/.ingredients/{}/config".format(HOSTNAME),
    ]:
        if path and os.path.exists(path):
            return path

def subcommand(name):
    try:
        return importlib.import_module("sub."+name).main
    except ImportError as e:
        subcommand("help")(code=1)
        raise e

