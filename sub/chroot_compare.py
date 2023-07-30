import os
import dir_config
import helpers
import subprocess
import sys

def parallel_walk(top1, top2, relative=""):
    """
    Returns pairs (path1, path2) from both trees.
    If a file is only in top1, (file, None) is returned
    If a file is only in top2, (None, file) is returned
    Don't recurse into symlinks.
    """
    try:
        entries1 = os.scandir(top1)
        entries2 = os.scandir(top2)
    except (PermissionError, FileNotFoundError):
        return
    names1 = { x.name: x for x in entries1 }
    names2 = { x.name: x for x in entries2 }
    for name in sorted(names1.keys() | names2.keys()):
        e1, e2 = names1.get(name), names2.get(name)
        r = (relative + "/" + name) if relative else name # Profiling says this is faster than os.path.join
        if e1 and e2 and e1.is_dir(follow_symlinks=False) and e2.is_dir(follow_symlinks=False):
            yield from parallel_walk(e1.path, e2.path, r)
        yield e1, e2, r

def sameFile(fileA, fileB):
    if fileA.stat(follow_symlinks=False).st_size != fileB.stat(follow_symlinks=False).st_size:
        return False
    return True
def differences(top1, top2, config, ignore="i"):
    different = set()
    for p1, p2, rel in parallel_walk(top1, top2):
        if (
            (p1 is None) or
            (p2 is None) or 
            (p1.is_symlink() + p2.is_symlink() == 1) or
            (p1.is_dir(follow_symlinks=False) + p2.is_dir(follow_symlinks=False) == 1) or
            (p1.is_file(follow_symlinks=False) + p2.is_file(follow_symlinks=False) == 1) or
            (p1.is_dir(follow_symlinks=False) and rel in different) or
            (p1.is_file(follow_symlinks=False) and not sameFile(p1, p2))
        ):
            if config.classify(rel) in ignore: continue
            yield p1, p2, rel
            #while rel:
                #different.add(rel)
                #rel = os.path.dirname(rel)

def get_owner(path):
    try:
        return subprocess.check_output(["pacman", "-Qoq", path], stderr=subprocess.DEVNULL).decode("utf8").strip()
    except subprocess.CalledProcessError:
        return "none"

def get_chroot_owner(chroot, path):
    try:
        return subprocess.check_output(["sudo", "arch-chroot", chroot, "pacman", "-Qoq", path], stderr=subprocess.DEVNULL).decode("utf8").strip()
    except subprocess.CalledProcessError:
        return "none"

def main(chroot, root="/", **options):
    config = dir_config.read_config()
    special = helpers.locate_config_dir()
    problems = 0
    for p1, p2, rel in differences(root, chroot, config, ignore="is"):
        c = config.classify(rel)
        if not os.path.exists(os.path.join(special, rel)) and not os.path.islink(os.path.join(special, rel)):
            direction = "?<>="[bool(p1)*2+bool(p2)]
            if (p1 or p2).is_symlink():                     typec="s"
            elif (p1 or p2).is_dir(follow_symlinks=False):  typec="d"
            elif (p1 or p2).is_file(follow_symlinks=False): typec="f"
            else:                                           typec="?"
            if p1: owner = get_owner(p1)
            else:  owner = get_chroot_owner(chroot, rel)
            problems += 1
            print("{} {} {} /{} (owner: {})".format(direction, typec, c, rel, owner))
    print("{} differences found".format(problems))
    sys.exit(problems>0)
