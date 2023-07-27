import sys

HELP = """Usage: za3kstrap SUBCOMMAND ...
    za3kstrap build-chroot
    za3kstrap help
        Display this message
    za3kstrap lint-packages
        Check whether the list of packages matches ~/.packages/<hostname>:~/.ingredients/<hostname>
            -v,--verbose Verbose output. Print passed checks as well as failed checks.
    za3kstrap list-packages
    (za3kstrap lint-dotfiles)
        Check whether the dotfiles match ~/.dot
    (za3kstrap lint-projects)
        Check whether the projects match ~/.projects
    za3kstrap lint
        Check whether the ingredients list can generate the current system image.
            -f,--fast Only do quick checks. <10ms
    za3kstrap make-packages
        TODO: Output Arch Linux packages in a format accepted by build-chroot, one per line.
    za3kstrap make-restore
    za3kstrap test-repro
    za3kstrap update-config
    za3kstrap update-state"""

def main(code=0):
    print(HELP)
    sys.exit(code)
