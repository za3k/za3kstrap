#!/usr/bin/env python3
import subprocess, sys
import helpers
from collections import defaultdict
from sub.lint_packages import *
from tqdm import tqdm

# Pacman helper functions
def get_possible_groups():
    out = subprocess.run(["pacman", "-Qg"], capture_output=True).stdout.decode("utf8")
    return set(line.split()[0] for line in out.strip().split("\n"))
def are_aur(packages):
    command = ["pacman", "-Qqm"] + list(packages)
    return set(subprocess.check_output(command, stderr=subprocess.DEVNULL).decode("utf8").strip().split("\n"))

def get_installed():
    actual_explicit_packages = get_explicit_packages()
    aur_packages = are_aur(actual_explicit_packages)
    return (actual_explicit_packages - aur_packages), aur_packages

def main(**options):
    print("# A list of installed packages on machine '{}'".format(helpers.HOSTNAME))
    packages, aur_packages = get_installed()
    for package in sorted(packages):
        print("{}".format(package))
    if aur_packages:
        print()
        print("# +yay means 'yay' is in the Arch User Repository")
        print("+yay")
    for package in sorted(aur_packages):
        print("+{}".format(package))
    possible_groups = sorted(get_possible_groups())
    if possible_groups:
        print()
        print("# *{} means '{}' is a package group".format(possible_groups[0], possible_groups[0]))
        print("# Arch Linux doesn't store information about which groups have been installed") 
        print("# Possible groups on your system include:")    
        for group in sorted(get_possible_groups()):
            print("# *{}".format(group))
