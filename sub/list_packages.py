#!/usr/bin/env python3
import helpers

def main(subset, **options):
    packages, groups, aur_packages = helpers.get_package_file(options.get("package_file"))
    out = {
        "all": packages + groups + aur_packages,
        "packages": packages,
        "aur": aur_packages,
        "regular": packages + groups,
        "groups": groups
    }[subset]
    for x in sorted(set(out)):
        print(x)
