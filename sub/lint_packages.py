#!/usr/bin/env python3
# TODO: Check whether the AUR + and * group match
import os, socket, subprocess, sys
from collections import defaultdict

problems = 0
def fail(msg):
    global problems
    problems += 1
    print("FATAL", msg)
    sys.exit(1)
def warn(msg):
    global problems
    problems += 1
    print("WARN", msg)
def ok(msg):
    print("OK", msg, file=sys.stderr)
def done():
    global problems
    if problems == 0:
        print("ok.", file=sys.stderr)
        sys.exit(0)
    else:
        print("dotfile linter: {} problems found".format(problems))
        sys.exit(2)

HOSTNAME=socket.gethostname()
def get_package_file(file=None):
    if file is None:
        file = "/home/zachary/.packages/{}".format(HOSTNAME)
    packages, groups = [], []
    with open(file) as f:
        for line in f:
            line = line.split("#")[0].strip().lstrip("+")
            if line == "":
                continue
            if line.startswith("*"):
                groups.append(line[1:])
            else:
                packages.append(line)
    return sorted(packages), sorted(groups)

# Pacman helper functions
def get_packages():
    stdout = subprocess.run(["pacman", "-Q"], capture_output=True).stdout.decode("utf8")
    packages = set()
    for line in stdout.rstrip().split("\n"):
        packages.add(line.split(" ")[0])
    return packages
def get_explicit_packages():
    stdout = subprocess.run(["pacman", "-Qe"], capture_output=True).stdout.decode("utf8")
    packages = set()
    for line in stdout.rstrip().split("\n"):
        packages.add(line.split(" ")[0])
    return packages
def get_group_contents(groups):
    stdout = subprocess.run(["pacman", "-Qg"] + groups, capture_output=True).stdout.decode("utf8")
    packages = defaultdict(set)
    for line in stdout.rstrip().split("\n"):
        group, package = line.split(" ")
        packages[group].add(package)
    return packages

if __name__ == "__main__":
    global verbose
    verbose=True
    main(os.environ.get("ARCH_PACKAGEFILE"))
    done()

def main(package_file=None):
    expected_packages, expected_groups = get_package_file(package_file)
    #print("Packages/groups read: ", expected_packages, expected_groups)
    group_packages = get_group_contents(expected_groups)
    expected_group_packages = [item for group in group_packages.values() for item in group]
    expected_flat_packages = sorted(set(expected_packages + expected_group_packages))
    #print("Flat packages list: ", expected_flat_packages)

    actual_packages = get_packages()
    actual_explicit_packages = get_explicit_packages()
    #print("Actual installed packages: ", actual_packages)

    for installed in sorted(actual_explicit_packages):
        if installed in expected_flat_packages:
            ok("Match: {}".format(installed))
        else:
            warn("Unexpected package: {}".format(installed))
    for expected in expected_packages:
        if expected in actual_packages:
            if expected in actual_explicit_packages:
                pass # already said "OK"
            else:
                warn("Package installed, but not explicitly: {}".format(expected))
        else:
            warn("Expected package not installed: {}".format(expected))
    for group in expected_groups:
        group_ok = True
        for expected in group_packages[group]:
            if expected in actual_packages:
                pass
            else:
                group_ok = False
        if group_ok:
            ok("Group: {}".format(group))
        else:
            warn("Some packages not present: {}".format(group))
