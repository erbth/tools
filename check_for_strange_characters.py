#!/usr/bin/python3
import sys
import os

ALLOWED_CHARS_DEF = \
"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" \
" \n\r\t" \
"!@#$%^&*()[]{}-=_+|\\;:'\",.<>/?`~"

ALLOWED_CHARS = [c.encode('ascii')[0] for c in ALLOWED_CHARS_DEF]


def check_char(c):
    if c not in ALLOWED_CHARS:
        print("Character not allowed: 0x%x" % (c,))
        return False

    return True


def main():
    error = False

    if len(sys.argv) != 2:
        print("Usage: %s <filename>" % sys.argv[0])
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        cnt_processed = 0
        file_size = os.fstat(f.fileno()).st_size

        while True:
            chunk = f.read(10000)
            if not chunk:
                break

            for c in chunk:
                ret = check_char(c)
                if not ret:
                    error = True

            cnt_processed += len(chunk)

    if error:
        print("Unallowed characters found")
        sys.exit(1)

    print("All characters allowed")


if __name__ == '__main__':
    main()
    sys.exit(0)
