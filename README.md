(**!WORK IN PROGRESS, NOT YET DONE!**)
za3kstrap (za3k's bootstrap) is a tool to manage Arch Linux installs.

It maintains a one-to-one correspondence between a working Arch Linux install,
and a **blueprint**, a small set of config files that can be used to generate
that working install.

Using blueprints also has the advantage of letting you keep several installs
in sync with one another, or examining semantic-level differences between
running systems.

### Capabilities

**(not yet done)** za3kstrap is capable of 
1. taking a running system and extracting a blueprint
2. taking a blueprint, and creating a running system.
3. (linters) keeping a blueprint up-to-date with a running system. za3kstrap
   will note any differences, and intelligently prompt to user to resolve them.
4. backing up important parts of a running system
5. restoring a running system after a fault
6. working with running systems, chroots, hard drives and USBs, and disk images

### Concepts

Conceptually, za3kstrap splits files and directories in an install into
  three classes:
- "config". Installed packages, services, config files, code, etc.
  Think /etc and /usr.
- "state". Working data. Home directories, databases, secret keys. Think /home.
- "ignore". Chromium caches, /tmp, logs. Think /tmp.

When performing a backup or restore
- The "ignore" class is ignored. We don't need to back up or restore /tmp
- The "config" class is treated semantically as possible. We'd like a list of
  packages to install, not a huge number of files to copy.
- The "state" is not examined. It's blindly treated as files to copy or restore.

za3kstrap breaks down a **recipe** as follows:
- DIRS, an explanation of which paths are "config", "state", or "ignore"
- ("config" class) PACKAGES, a list of installed packages (normal, AUR
  packages, and package groups)
- ("config" class) 'config.tar', config files which don't match the system
  defaults and should be used in their place

### Linter examples

If you newly install a package, za3kstrap will prompt:

    WARN Unexpected package: mpv
    A=Add package to list, U=Uninstall package, or S=Skip? (A,u,s)

If you remove a package, za3kstrap will prompt:

    WARN Expected package not installed: mplayer
    I=Install package, R=Remove from package list, or S=Skip? (i,r,S) 

If you change a config file on the running system, za3kstrap will prompt:

    WARN Modified config file: /etc/fstab
    M=Modify declarative file, R=Revert system version, D=Show diff, or
        S=Skip? (M,r,d,s)

If you add a cronjob, za3kstrap will prompt:

    WARN New config file: /etc/cron.daily/backup
    A=Add declarative file, U=Uninstall file, or S=Skip? (A,u,s)

If you enable a system service, za3kstrap will prompt:

    WARN New config file: /etc/systemd/system/multi-user.target.wants/
        nullmailer.service
    A=Add declarative file, U=Uninstall file, or S=Skip? (A,u,s)

### Usage

```
Usage: za3kstrap SUBCOMMAND ...
    za3kstrap make-packages
        Print packages found on the host, in the PACKAGES format, one per line.

    za3kstrap list-packages [all|packages|regular|aur|groups]
        Prints packages found in the PACKAGES file, one per line.

    za3kstrap update-config
        TODO: Updates ~/.ingredients/<hostname>/config, clobbering anything there

    (za3kstrap update-state [STATE-OPTIONS])
        TODO: Backup state (not at all / from host system / from given backup directory / over rsync)

    za3kstrap make-restore [STATE-OPTIONS] TARGET
        TODO: Generate a folder containing a script that can chroot-build a working system

    za3kstrap test-repro [STATE-OPTIONS] CHROOT
        TODO: Check whether the ingredients list can generate the current system image.
        Calls in order: chroot-build, chroot-compare

    za3kstrap chroot-build [STATE-OPTIONS] CHROOT
        TODO: Calls: chroot-add-packages, chroot-add-config, chroot-add-state
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

    General options:
        -v, --verbose: Increase verbosity
        -q, --quiet:   Reduce verbosity
        -s, --silent:  Don't output anything to stdout/stderr
    chroot options:
        CHROOT:        Path to the chroot to build, update, or check
    linter options
        -f, --fast:    Only run very fast linters (<100ms). Useful for regular checks
        --full:        Run all linters.
        --periodic:    (Default) Always run fast linters, and run other linters if it's been a while.
    state options:
        TODO
```
