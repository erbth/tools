#!/usr/bin/python3
import os
import re
import subprocess
import sys
from urllib import parse


def format_fpr(fpr):
    fpr = [fpr[i*4:(i+1)*4] for i in range(10)]
    fpr = fpr[:5] + [''] + fpr[5:]
    return ' '.join(fpr)

def unescape(s):
    return s.encode('latin-1').decode('unicode_escape')

def sources_lists_contain_keyring(k):
    for s in ['/etc/apt/sources.list', *[os.path.join('/etc/apt/sources.list.d', f)
            for f in os.listdir('/etc/apt/sources.list.d')]]:
        with open(s, 'r', encoding='utf8') as f:
            for line in f:
                m = re.match(r'.*signed-by=([^\t \n\r\]]*)(?:\s|\])', line)
                if m and m[1].strip('"') == k:
                    return True

    return False

def sorting_key(l):
    m = re.fullmatch(r'(?:[0-9A-F]{4}\s+){10}(\S+)  (.*)', l)
    filename = m[1]
    uid = m[2]

    k = ''
    k2 = 9999999999
    if filename.startswith('debian-'):
        k += '000'
        m2 = re.match(r'.*\((\d+)/', uid)
        if m2:
            k2 -= int(m2[1])

    elif filename.startswith('local'):
        k += '001'

    elif filename.startswith('microsoft'):
        k += '002'

    elif filename.startswith('atom'):
        k += '003'

    elif filename.startswith('ceph'):
        k += '004'

    else:
        k += '999'

    return (k, k2, filename)


def main():
    keyrings = []
    output = []

    if os.path.isfile('/etc/apt/trusted.gpg'):
        keyrings.append('/etc/apt/trusted.gpg')

    for f in os.listdir('/etc/apt/trusted.gpg.d'):
        keyrings.append(os.path.join('/etc/apt/trusted.gpg.d', f))

    for f in os.listdir('/usr/share/keyrings'):
        # Filter only used keyrings
        k = os.path.join('/usr/share/keyrings', f)
        if not sources_lists_contain_keyring(k):
            print("Skipping keyring '%s' (not used)." % k, file=sys.stderr)
            continue

        keyrings.append(k)

    for keyring in keyrings:
        ret = subprocess.run(['gpg', '--keyring', keyring, '--no-default-keyring',
            '--list-keys', '--with-colons'], stdout=subprocess.PIPE)

        if ret.returncode != 0:
            print("Invalid keyring file '%s'" % keyring)
            sys.exit(1)

        fpr = None
        uid = None

        for l in ret.stdout.decode('utf8').splitlines():
            if l.startswith('fpr:'):
                fpr = l.split(':')[9]

            elif l.startswith('uid'):
                uid = unescape(l.split(':')[9])
                if fpr is None:
                    print("Keyring file '%s' has a user-id without a fingerprint" % keyring)
                    sys.exit(1)

                output.append("%s %s  %s" % (format_fpr(fpr), os.path.basename(keyring), uid))
                uid = None
                fpr = None

    output.sort(key=sorting_key)
    last = None

    for line in output:
        if last != line:
            print(line)

        last = line

    sys.exit(0)


if __name__ == '__main__':
    main()
