#!/usr/bin/env python3
import helpers

import contextlib
import glob
import logging
import os
import shlex
import subprocess
import time

def shell_quote(cmd):
    return " ".join(shlex.quote(arg) for arg in cmd)
def in_chroot(root, *cmds, user='root', **vargs):
    if len(cmds) == 1:
        cmd = cmds[0]
    else:
        assert len(cmds) >= 1
        cmd = ["bash", "-c", ' && '.join(shell_quote(cmd) for cmd in cmds)]
    if user != 'root':
        cmd = ["sudo", "-u", user, "--"] + cmd
    cmd = ["arch-chroot", root] + cmd
    return run(cmd, sudo=True, **vargs)

def append(root, path, line):
    if in_chroot(root, ["grep", "-q", "-x", line, path]).returncode == 0:
        logging.debug("append: line already present")
        return
    logging.debug("append: line not present, appending")
    line += "\n"
    in_chroot(root, ["tee", "-a", path], input=line, encoding="ascii")

def run(cmd, sudo=False, **vargs):
    if sudo:
        cmd = ["sudo", "--"] + cmd
    logging.debug(cmd)
    return subprocess.run(cmd, **vargs)

def glob_chroot(root, *paths):
    if paths[0].startswith("/"):
        paths = (paths[0][1:],) + paths[1:]
    path = glob_one(os.path.join(root, *paths))
    return os.path.relpath(path, root)
def glob_one(path):
    res = glob.glob(os.path.expanduser(path))
    return res[0] if res else None

def task_update_host():
    logging.info("packages: update host")
    run(["pacman", "-Syu"], sudo=True)

    # Remove orphans? sudo pacman -Qqttd | sudo pacman -Rns -

def task_copy_cache(root):
    logging.info("packages: cleanup host cache")
    run(["pacman", "-Sc", "--noconfirm"], sudo=True)
    logging.info("packages: copy host cache")
    target = os.path.join(root, "var/cache/pacman/pkg")
    logging.debug(target)
    run(["mkdir", "-p", target], sudo=True)
    run(["cp", "-a", "-T", "/var/cache/pacman/pkg", target], sudo=True)

@contextlib.contextmanager
def task_bind_mount(root):
    if run(["mountpoint", "-q", root]).returncode == 0:
        yield
    else:
        # Bind-mount /repro if not already a mount
        logging.info("chroot: disguising root as a mount")
        run(["mount", "--bind", root, root], sudo=True)
        yield
        # Unbind /repro
        logging.info("chroot: undisguising root as a mount")
        run(["sudo", "umount", "-t", "bind", "-q", root])

def task_install_regular_packages(root, package_file=None):
    logging.info("packages: install from core/extra/multilib")
    packages, groups, aur_packages = helpers.get_package_file(package_file)
    run(["pacstrap", "-c", root] + packages + groups, sudo=True)

def task_install_yay(root):
    yay_package = glob_one("~/.cache/yay/yay/*.pkg.tar.zst") # Copy an existing install if we have it
    if yay_package:
        logging.info("packages: copy yay package from host")
        run(["cp", yay_package, os.path.join(root, "var/cache/pacman/pkg")], sudo=True)
    else:
        logging.info("packages: build yay from PKGBUILD")
        build_dir="/var/tmp/yay"
        in_chroot(root, ["git", "clone", "https://aur.archlinux.org/yay.git", build_dir],
                        ["cd", build_dir],
                        ["env", "GOCACHE=/tmp", "makepkg"], # Don't try to write to /, nobody's homedir
                        user='nobody')
        yay_package = glob_chroot(root, build_dir, "yay-*.pkg.tar.zst")
        in_chroot(root, ["cp", yay_package, "/var/cache/pacman/pkg"])
        in_chroot(root, ["rm", "-r", build_dir])
    logging.info("packages: install yay using ABS")
    yay_package = glob_chroot(root, "/var/cache/pacman/pkg", "yay-*.pkg.tar.zst")
    in_chroot(root, ["pacman", "-U", "--noconfirm", yay_package])
    in_chroot(root, ["rm", yay_package])

def task_make_aur_user(root):
    logging.info("packages: create aur user")
    in_chroot(root, ["useradd", "aur", "-m", "-c", "Used to call yay", "-s", "/bin/false", "-G", "wheel"])
    logging.info("sudo: allow passwordless sudo")
    append(root, "/etc/sudoers", "%wheel ALL=(ALL) NOPASSWD: ALL")

def task_copy_cache_aur(root):
    logging.info("packages: copy host yay cache")
    target = os.path.join(root, "home/aur/.cache/yay")
    run(["mkdir", "-p", target], sudo=True)
    run(["cp", "-a", "-T", glob_one("~/.cache/yay"), target], sudo=True)
    in_chroot(root, ["chown", "-R", "aur:aur", "/home/aur"])

def task_install_aur_packages(root, package_file=None):
    logging.info("packages: install from aur")
    packages, groups, aur_packages = helpers.get_package_file(package_file)
    aur_packages = sorted(set(aur_packages) - {"yay-git", "yay"}) # No need to reinstall yay!
    in_chroot(root, ["yay", "-S", 
        #"--answerclean", "All", # Do a clean install of everything
        "--answerclean", "None",
        "--nodiffmenu", # Don't show diffs
        "--removemake", # Remove make dependencies
        "--noconfirm", # auto-install and accept PGP keys
    ] + aur_packages, user='aur')
    in_chroot(root, ["pacman", "-Sc", "--noconfirm"])

def with_timer(name, f, elapsed={}):
    def inner(*args, **vargs):
        start = time.perf_counter()
        ret = f(*args, **vargs)
        elapsed[name] = time.perf_counter() - start
        logging.info(elapsed)
        return ret
    return inner


for x in [x for x in globals() if x.startswith("task_")]:
    globals()[x] = with_timer(x, globals()[x])

def main(root, package_file=None, **options):
    with task_bind_mount(root):
        task_update_host() # So we can copy the cache better
        task_copy_cache(root)
        task_install_regular_packages(root, package_file=package_file)
        task_install_yay(root)

        task_make_aur_user(root)
        task_copy_cache_aur(root)
        task_install_aur_packages(root, package_file=package_file)
        # Set up config files
        #task_set_locale(root)
