import helpers
import sys

def main(**options):
    ok = True
    sys.stderr.write("Linting packages... ")
    if helpers.subcommand("lint_packages")(quiet=True, silent=True):
        sys.stderr.write("ok\n")
    else:
        sys.stderr.write("failed\n")
        ok = False
        sys.exit(2)
    print("Linting dotfiles... not implemented", file=sys.stderr)
    print("Linting projects... not implemented", file=sys.stderr)
    print("Linting repro (may take a while)... not implemented", file=sys.stderr)
    print("Lint failed because it is not implemented")
    sys.exit(1)
