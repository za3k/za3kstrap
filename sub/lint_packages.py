#!/usr/bin/env python3
# TODO: Check whether the AUR + and * group match
import os, subprocess, sys
import helpers
from collections import defaultdict

problems = 0
fixed = 0
def fail(msg, verbosity=2):
    global problems
    problems += 1
    print("FATAL", msg)
    sys.exit(1)
def warn(msg, verbosity=2):
    global problems
    problems += 1
    print("WARN", msg)
def ok(msg, verbosity=2):
    if verbosity >= 3:
        print("OK", msg, file=sys.stderr)
def done(verbosity=2):
    # Returns whether everything is OK
    global fixed, problems
    if problems + fixed == 0:
        if verbosity >= 3:
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
    command = ["yay", "-S", package]
    subprocess.run(command)
    return True
def uninstall_package(package):
    command = ["sudo", "pacman", "-Rs", package]
    subprocess.run(command)
    return True
def makeexplicit_package(package):
    command = ["sudo", "pacman", "-D", "--asexplicit", package]
    subprocess.run(command)
    return True
def is_aur(package):
    command = ["pacman", "-Qqm", package] # Already does exact match
    return subprocess.run(
        command,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL).returncode == 0
def add_package(package_file, package):
    if is_aur(package):
        package = "+" + package
    with open(package_file, "a") as f:
        print(package, file=f)
    return True
def line_is_package(line, package):
    line = line.split("#")[0]
    line = line.strip("*+ \n")
    return package == line
def remove_package(package_file, package):
    with open(package_file, "r") as f:
        lines = [line for line in f]
    matching_lines = [line for line in lines if line_is_package(line, package)]
    if len(matching_lines) == 0:
        print("Package not found to remove (comment out): {}".format(package)) 
        return False
    elif len(matching_lines) > 1:
        print("Multiple copies of package found to remove (comment out): {}".format(package)) 
        return False
    assert len(matching_lines) == 1
    
    with open(package_file + ".tmp", "w") as outp:
        with open(package_file, "r") as inp:
            for line in inp:
                if line_is_package(line, package):
                    outp.write("#" + line.rstrip("\n") + " # removed by linter\n")
                else:
                    outp.write(line)
    os.replace(package_file + ".tmp", package_file)
    return True

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

@fix_decorator("E=Mark as explicitly installed, R=Remove from package list, or S=Skip?", "e", "r", "s", default="e")
def makeexplicit_or_remove_package_fix(package_file, package, choice):
    if choice == "e":
        return makeexplicit_package(package)
    elif choice == "r":
        return remove_package(package_file, package)
    elif choice == "s":
        return False

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
    package_file = helpers.locate_package_file(file=package_file)
    assert package_file is not None, "Package file not found"
    expected_packages, expected_groups, expected_aur_packages = helpers.load_package_file(package_file)
    #print("Packages/groups read: ", expected_packages, expected_groups)
    group_packages = get_group_contents(expected_groups)
    expected_group_packages = [item for group in group_packages.values() for item in group]
    expected_flat_packages = sorted(set(expected_packages + expected_aur_packages + expected_group_packages))
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
                yield warn, "Package installed, but not explicitly: {}".format(expected), makeexplicit_or_remove_package_fix(package_file, expected)
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

def main(package_file=None, verbosity=1, make_changes=True, interactive=True, **args):
    for level, problem, fix in lint(package_file=package_file):
        if 0 == verbosity:
            continue
        if 1 == verbosity and level==ok:
            continue
        level(problem, verbosity=verbosity)
        if fix and make_changes:
            fix(interactive=interactive)
    return done(verbosity=verbosity)
