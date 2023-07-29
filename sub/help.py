import sys

HELP = """Usage: za3kstrap SUBCOMMAND ...
    za3kstrap make-packages
        Print packages found on the host, in the PACKAGES format, one per line.

    za3kstrap list-packages (all|packages|regular|aur|groups)
        Prints packages found in the PACKAGES file, one per line.

    za3kstrap update-config
        TODO: Updates ~/.ingredients/<hostname>/config, clobbering anything there

    (za3kstrap update-state [STATE-OPTIONS])
        TODO: Backup state (not at all / from host system / from given backup directory / over rsync)

    za3kstrap make-restore [STATE-OPTIONS] TARGET
        TODO: Generate a folder containing a script that can chroot-build a working system

    za3kstrap test-repro [STATE-OPTIONS] CHROOT
        Check whether the ingredients list can generate the current system image.
        Calls in order: chroot-build, chroot-compare

    za3kstrap chroot-build [STATE-OPTIONS] CHROOT
        Calls: chroot-add-packages, chroot-add-config, chroot-add-state
    za3kstrap chroot-add-packages CHROOT
        Install Arch Linux packages from ~/.ingredients/<hostname>/PACKAGES
    za3kstrap chroot-add-config CHROOT
        TODO: Install config files from ~/.ingredients/<hostname>/config
    za3kstrap chroot-add-state CHROOT
        TODO: Can restore state (not at all / from host system / from given backup directory / over rsync)
    (za3kstrap chroot-add-dotfiles CHROOT)
        TODO
    (za3kstrap chroot-add-projects CHROOT)
        TODO
    za3kstrap chroot-compare CHROOT
        Compares a chroot with the host image, and reports any differences. (Checks file size instead of hashing for speed)
        TODO: Mostly done, needs status code

    za3kstrap lint
        Check common errors for whether the ingredients list can generate the current system image.
        For a full test, run test-repro
            -f,--fast Only do quick checks. <10ms
        Calls: lint-packages, lint-config, lint-state, lint-dotfiles, lint-projects
    za3kstrap lint-packages
        Check whether host packages match ~/.ingredients/<hostname>/PACKAGES
            -v,--verbose Verbose output. Print passed checks as well as failed checks.
    za3kstrap lint-config
        TODO: Check whether host config files match ~/.ingredients/<hostname>config
    (za3kstrap lint-dotfiles)
        TODO: Check whether the dotfiles match ~/.dot
    (za3kstrap lint-projects)
        TODO: Check whether the projects match ~/.projects
    za3kstrap lint-state
        TODO

    za3kstrap help
        Display this message
"""

def main(code=0):
    print(HELP)
    sys.exit(code)
