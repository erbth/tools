#!/usr/bin/python3
import argparse
import os
import re
import stat
import sys


# Fullmatch-regular expressions
RULES = [
    r'.*\.class',
    r'.*\.jar',
    r'.*\.jpi',
    r'.*\.hpi',
    r'.*\.war',
    r'.*\.ear',
    r'.*\.aar',

    # NOTE: Not sure if .zip files can actually be used automatically by java
    # without 'exploding' them first
    r'.*\.zip'
]


def scan_file(f, rules, cfg, dev=None, ignore_nonexistent=True):
    try:
        s = os.lstat(f)
    except FileNotFoundError:
        if ignore_nonexistent:
            print("  File '%s' vanished." % f, file=sys.stderr)
            return False

        raise

    if cfg['same_fs']:
        if dev is None:
            dev = s.st_dev

        elif dev != s.st_dev:
            print("  Not descending into filesystem mounted on '%s'." % f, file=sys.stderr)
            return False

    if stat.S_ISDIR(s.st_mode):
        found = False
        for c in os.listdir(f):
            if scan_file(os.path.join(f, c), rules, cfg, dev):
                found = True

        return found

    else:
        for r in rules:
            if r.fullmatch(os.path.basename(f)):
                print(str(f))
                return True

        return False

    raise RuntimeError("Saved your life.")


def main():
    parser = argparse.ArgumentParser("Find java files in the specified directories")
    parser.add_argument("directories", metavar="<directory>",
        type=str, nargs="+", help="directories to examine")

    parser.add_argument("--same-fs", action="store_true", help="Do not descend into mountpoints")

    args = parser.parse_args()
    rules = [re.compile(r) for r in RULES]

    cfg = {
        'same_fs': args.same_fs
    }

    found = False
    for d in args.directories:
        if scan_file(d, rules, cfg, ignore_nonexistent=False):
            found = True

    sys.exit(0 if found else 1)


if __name__ == '__main__':
    main()
