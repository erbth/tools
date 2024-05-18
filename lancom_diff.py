#!/usr/bin/python3
import re
import sys


def print_dict_diff(d1, d2, indent='    '):
    for k in sorted(set(d1.keys()) | d2.keys()):
        if k not in d1:
            print("%s%s only in 2" % (indent, k))
        elif k not in d2:
            print("%s%s only in 1" % (indent, k))
        elif d1[k] != d2[k]:
            print("%s%s differs: %s != %s" % (indent, k, d1[k], d2[k]))


def print_list_diff(l1, l2):
    m = 0
    n = 0
    while m < len(l1) or n < len(l2):
        if m < len(l1):
            v1 = l1[m]

        if n < len(l2):
            v2 = l2[n]

        if v1 == v2:
            m += 1
            n += 1
            continue

        # Try to find v1 in l2
        found = False
        for j in range(n+1, len(l2)):
            if l2[j] == v1:
                for k in range(n, j):
                    print("    only in 2 (pos %d): %s" % (k, l2[k]))

                n = j+1
                m += 1
                found = True
                break

        if found:
            continue

        # Try to find v2 in l1
        found = False
        for j in range(n+1, len(l1)):
            if l1[j] == v2:
                for k in range(n, j):
                    print("    only in 1 (pos %d): %s" % (k, l1[k]))

                m = j+1
                n += 1
                found = True
                break

        if found:
            continue

        # Two differing entries
        if m < len(l1) and n < len(l2):
            print("    %s (1 pos: %d) != %s (2 pos: %d)" % (v1, m, v2, n))
            print_dict_diff(v1, v2, indent='        ')

            m += 1
            n += 1
            continue

        # End-of-list cases
        if m < len(l1):
            print("    only in 1 (pos %d): %s" % (m, v1))
            m += 1
            continue

        if n < len(l2):
            print("    only in 2 (pos %d): %s" % (n, v2))
            n += 1
            continue

        raise RuntimeError("Diff algorithm fault")


def parse(lines):
    info = {}
    cfg = []
    state = 0
    stack = []

    _re_listentry = r"\(((?:\d+\.)*\d+)\)\s+=(?:((?:\s+.*)|(?:=(?:\s.*)?)))?"

    def _parse_nonspecial(line):
        nonlocal stack, state
        if re.fullmatch(r"{[^{}]+}", line):
            return

        m = re.fullmatch(r"((?:\d+\.)*\d+)\s+=(?:((?:\s.*)|(?:=(?:\s.*)?)))?", line)
        if m:
            cfg.append((m[1], m[2]))
            return

        m = re.fullmatch(r"<((?:\d+\.)*\d+)>", line)
        if m:
            stack.append(m[1])
            stack.append([])
            state = 20
            return

        raise ValueError("Invalid line: `%s'" % line)

    def _emit_list():
        nonlocal stack, state
        cfg.append((stack[-2], stack[-1]))
        stack = stack[:-2]
        state = 10


    for line in lines:
        line = line.lstrip().rstrip('\n\r')

        if state == 0:
            m = re.fullmatch(r'\((.*)\)', line)
            if not m:
                raise ValueError("Invalid first line")

            info['comment'] = m[1]
            state = 1

        elif state == 1:
            m = re.fullmatch(r'\((.+)\s+/\s+(.+)\)', line)
            if not m:
                raise ValueError("Invalid second line")

            info['version_comment'] = m[1]
            state = 2

        elif state == 2:
            m = re.fullmatch(r'\[(.*)\]\s+(\S+)\s+/\s+(\S+)\s+(\S+)', line)
            if not m:
                raise ValueError("Invalid third line")

            info['device'] = m[1]
            info['version'] = m[2]
            info['version_date'] = m[3]
            info['version_date_short'] = m[4]
            state = 10


        elif state == 10:
            _parse_nonspecial(line)

        elif state == 20:
            m = re.match(_re_listentry, line)
            if m:
                stack[-1].append((m[1], m[2]))
                continue

            _emit_list()
            _parse_nonspecial(line)

    if state != 10:
        raise ValueError("Stopped in non-terminal state")

    # Interpret values
    def _interpret_val(v):
        if v.startswith("= "):
            return "enc:" + v[2:]
        elif v.startswith(" "):
            return v[1:]
        else:
            raise ValueError("Invalid string literal (does not start with '= ' or ' ')")

    _cfg = cfg
    cfg = {}
    for k, v in _cfg:
        if isinstance(v, str):
            if v in cfg:
                raise ValueError("Duplicate value for %s" % v)

            cfg[k] = _interpret_val(v)

        elif isinstance(v, list):
            if k not in cfg:
                cfg[k] = []

            if v:
                cfg[k].append({
                    int(k2[k2.rfind('.')+1:]): _interpret_val(v2)
                    for k2, v2 in v
                })

        else:
            raise RuntimeError("Invalid cfg value")

    return info, cfg

def main():
    if len(sys.argv) != 3:
        print("Usage: %s <file 1> <file 2>" % sys.argv[0])
        sys.exit(2)

    with open(sys.argv[1], 'r', encoding='utf8') as f:
        lines1 = f.readlines()

    with open(sys.argv[2], 'r', encoding='utf8') as f:
        lines2 = f.readlines()

    info1, cfg1 = parse(lines1)
    info2, cfg2 = parse(lines2)


    # Compare configuration information
    info_for_cmp1 = dict(info1)
    info_for_cmp2 = dict(info2)

    del info_for_cmp1['comment']
    del info_for_cmp2['comment']

    if info_for_cmp1 != info_for_cmp2:
        print("Cfg information missmatch:")
        print_dict_diff(info_for_cmp1, info_for_cmp2)


    # Compare configurations
    for k in sorted(set(cfg1.keys()) | set(cfg2.keys())):
        if k not in cfg1:
            print("%s only in 2" % k)
            continue

        if k not in cfg2:
            print("%s only in 1" % k)
            continue

        v1 = cfg1[k]
        v2 = cfg2[k]

        if type(v1) != type(v2):
            print("%s: different types (1: %s, 2: %s)" % (k, type(v1), type(v2)))

        if isinstance(v1, str):
            if v1 != v2:
                print("%s: %s (1) != %s (2)" % (k, v1, v2))

        elif isinstance(v1, list):
            if v1 != v2:
                print("%s: lists differ:" % k)
                print_list_diff(v1, v2)

        else:
            raise RuntimeError("Invalid value type: %s" % (type(v1),))


if __name__ == '__main__':
    main()
    sys.exit(0)
