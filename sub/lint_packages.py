#!/usr/bin/env python3
# TODO: Check whether the AUR + and * group match
import os, socket, subprocess, sys
from collections import defaultdict

problems = 0
fixed = 0
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
    # Returns whether everything is OK
    global fixed, problems
    if problems + fixed == 0:
        if not quiet:
            print("ok.", file=sys.stderr)
        return True
    elif problems == 0:
        print("ok. {} problems fixed".format(fixed), file=sys.stderr)
        return True
    else:
        print("dotfile linter: {} problems remaining, {} fixed".format(problems, fixed))
        return False

def fix_decorator(prompt, *choices, default=None):
    assert default is not None
    for choice in choices:
        assert choice.islower()
        assert len(choice) == 1
    assert default.islower()
    assert default in choices
    prompt += " (" + ",".join([(x.upper() if x == default else x) for x in choices]) + ") "

    def _decorator(fixer):
        def _inner(*args):
            def _inner2(interactive):
                if not interactive:
                    return
                answer = "X"
                while answer[0] not in choices:
                    answer = input(prompt).lower()
                    if answer == "":
                        answer = default
                was_fixed = fixer(*args, choice=answer)
                if was_fixed:
                    global fixed, problems
                    fixed += 1
                    problems -= 1
            return _inner2
        return _inner
    return _decorator

def install_package(package):
    print("Not implemented: Install")
    return False
def uninstall_package(package):
    print("Not implemented: Uninstall")
    return False
def add_package(package_file, package):
    # TODO: Deal with AUR packages. Right now fix will fail for them.
    with open(package_file, "a") as f:
        print(package, file=f)
    return True
def remove_package(package_file, package):
    print("Not implemented: Remove (comment out) package")
    return False

@fix_decorator("A=Add package to list, U=Uninstall package, or S=Skip?", "a", "u", "s", default="a")
def add_or_uninstall_package_fix(package_file, package, choice):
    if choice == "a":
        return add_package(package_file, package)
    elif choice == "u":
        return uninstall_package(package)
    else:
        return False

@fix_decorator("Install package/group now?", "y", "n", default="y")
def install_package_fix(package_file, package, choice):
    if choice == "y":
        return install_package(package)
    else:
        return False

@fix_decorator("I=Install package, R=Remove from package list, or S=Skip?", "i", "r", "s", default="s")
def install_or_remove_package_fix(package_file, package, choice):
    if choice == "i":
        return install_package(package)
    elif choice == "r":
        return remove_package(package_file, package)
    elif choice == "s":
        return False

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
    packages, groups = [], []
    with open(package_file) as f:
        for line in f:
            line = line.split("#")[0].strip().lstrip("+")
            if line == "":
                continue
            if line.startswith("*"):
                groups.append(line[1:])
            else:
                packages.append(line)
    return sorted(packages), sorted(groups)
def get_package_file(file=None):
    package_file = locate_package_file(file=file)
    assert package_file is not None, "Package file not found"
    return load_package_file(package_file)

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
    package_file = locate_package_file(package_file)
    assert package_file is not None, "Package file not found"
    expected_packages, expected_groups = load_package_file(package_file)
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
            yield ok, "Match: {}".format(installed), None
        else:
            yield warn, "Unexpected package: {}".format(installed), add_or_uninstall_package_fix(package_file, installed)
    for expected in expected_packages:
        if expected in actual_packages:
            if expected in actual_explicit_packages:
                pass # already said "OK"
            else:
                yield warn, "Package installed, but not explicitly: {}".format(expected), install_package_fix(package_file, expected)
        else:
            yield warn, "Expected package not installed: {}".format(expected), install_or_remove_package_fix(package_file, expected)
    for group in expected_groups:
        group_ok = True
        for expected in group_packages[group]:
            if expected in actual_packages:
                pass
            else:
                group_ok = False
        if group_ok:
            yield ok, "Group: {}".format(group), None
        else:
            yield warn, "Some packages not present: {}".format("*"+group), install_package_fix(package_file, expected)

def lint_ok(*args, **kwargs):
    for level, problem in lint(*args, **kwargs):
        if level == ok:
            pass
        else:
            return False
    return True

def main(package_file=None, quiet=True, silent=False, make_changes=True, interactive=True):
    for level, problem, fix in lint(package_file=package_file):
        if silent:
            continue
        if quiet and level==ok:
            continue
        level(problem, quiet=quiet)
        if fix and make_changes:
            fix(interactive=interactive)
    return done(quiet=quiet)

if __name__ == "__main__":
    if main(os.environ.get("ARCH_PACKAGEFILE"), quiet=False):
        sys.exit(0)
    else:
        sys.exit(2)
