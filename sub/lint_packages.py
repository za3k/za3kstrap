#!/usr/bin/env python3
# TODO: Check whether the AUR + and * group match
import os, socket, subprocess, sys
from collections import defaultdict

problems = 0
def fail(msg, quiet=True):
    global problems
    problems += 1
    print("FATAL", msg)
    sys.exit(1)
def warn(msg, quiet=True):
    global problems
    problems += 1
    print("WARN", msg)
def ok(msg, quiet=True):
    if not quiet:
        print("OK", msg, file=sys.stderr)
def done(quiet=True):
    global problems
    if problems == 0:
        if not quiet:
            print("ok.", file=sys.stderr)
        sys.exit(0)
    else:
        print("dotfile linter: {} problems found".format(problems))
        sys.exit(2)

HOSTNAME=socket.gethostname()
def get_package_file(file=None):
    if file is None:
        for path in ["/home/zachary/.packages/{}", "/home/zachary/.ingredients/{}/PACKAGES"]:
            file = path.format(HOSTNAME)
            if os.path.exists(file):
                break
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

def lint(package_file=None):
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
            yield ok, "Match: {}".format(installed)
        else:
            yield warn, "Unexpected package: {}".format(installed)
    for expected in expected_packages:
        if expected in actual_packages:
            if expected in actual_explicit_packages:
                pass # already said "OK"
            else:
                yield warn, "Package installed, but not explicitly: {}".format(expected)
        else:
            yield warn, "Expected package not installed: {}".format(expected)
    for group in expected_groups:
        group_ok = True
        for expected in group_packages[group]:
            if expected in actual_packages:
                pass
            else:
                group_ok = False
        if group_ok:
            yield ok, "Group: {}".format(group)
        else:
            yield warn, "Some packages not present: {}".format(group)

def lint_ok(*args, **kwargs):
    for level, problem in lint(*args, **kwargs):
        if level == ok:
            pass
        else:
            return False
    return True

def main(package_file=None, quiet=True):
    for level, problem in lint(package_file=package_file):
        if quiet and level==ok:
            continue
        level(problem, quiet=quiet)
    done(quiet=quiet)

if __name__ == "__main__":
    main(os.environ.get("ARCH_PACKAGEFILE"), quiet=False)
