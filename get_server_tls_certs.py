#!/usr/bin/env python3
import subprocess
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <server[:port]>" % sys.argv[0])
        exit(1)

    ps = sys.argv[1].split(':')
    if len(ps) > 1:
        hostname = ':'.join(ps[:-1])
        port = ps[-1]
    else:
        hostname = ps[0]
        port = 443

    ret = subprocess.run([
            'openssl',
            's_client',
            '-showcerts',
            '-connect', '%s:%s' % (hostname, port),
            '-servername', hostname
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL)

    if ret.returncode != 0:
        print("OpenSSL s_client failed.")
        exit(ret.returncode)

    pem = b''
    in_cert = False

    for l in ret.stdout.split(b'\n'):
        l = l.strip()
        if not l:
            continue

        if l == b'-----BEGIN CERTIFICATE-----':
            in_cert = True
            pem += l + b'\n'
        elif l == b'-----END CERTIFICATE-----':
            in_cert = False
            pem += l + b'\n'
        elif in_cert:
            pem += l + b'\n'

    print(pem.decode('ascii'), end='')


if __name__ == '__main__':
    main()
    exit(0)
