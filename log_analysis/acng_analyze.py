#!/usr/bin/python3
import datetime
import glob
import os
import re
import socket
import sys


LOG_FILE_PATH = '/var/log/apt-cacher-ng'
VERBOSE = True
RESOLVE = True


class Timerange:
    def __init__(self):
        self._tss = set()

    def add(self, t):
        if not isinstance(t, datetime.datetime):
            raise ValueError("Can only add datetime.datetime objects")
        self._tss.add(t)

    def begin(self):
        return min(self._tss)

    def end(self):
        return max(self._tss)

    def __len__(self):
        return len(self._tss)


def ip_sort_key(ip):
    k = ''

    if ip.startswith('[INTERNAL:'):
        k += '0'
    elif ':' in ip:
        k += '2'
    else:
        k += '1'

    if ip.startswith('127') or ip == '::1':
        k += '0'
    else:
        k += '1'

    return k + ip


def read_acng_log(filename, log_output=sys.stdout):
    """
    Returns:
    [{
        'timestamp': :datetime,
        'dir': in|out|error,
        'size: transferred size / bytes,
        'ip': client ip,
        'filename': requested filename
    }}
    """
    records = []

    with open(filename, 'r', encoding='utf8') as f:
        lineno = 0
        for line in f:
            lineno += 1

            try:
                t = line.split('|')
                if len(t) != 5:
                    raise ParseError

                ts, inout, size, ip, fn = t
                try:
                    records.append({
                        'timestamp': datetime.datetime.fromtimestamp(int(ts)),
                        'dir': {'O': 'out', 'I': 'in', 'E': 'error'}[inout],
                        'size': size,
                        'ip': ip,
                        'filename': fn
                    })

                except (ValueError, OverflowError, KeyError) as e:
                    raise ParseError from e

            except ParseError:
                print('Invalid line %d in log file "%s" - ignoring.' % (lineno, filename),
                        file=log_output)

    if VERBOSE:
        print('Read %d records from "%s".' % (len(records), filename))

    return records


def read_acng_logs(path, log_output=sys.stdout):
    records = []
    for filename in sorted(glob.glob(os.path.join(path, 'apt-cacher.log*')), reverse=True):
        filename = os.path.abspath(filename)
        records += read_acng_log(filename, log_output)

    return records


def analyze_find_log_timeframe(records):
    a = None
    b = None

    for r in records:
        t = r['timestamp']
        if a is None or t < a:
            a = t

        if b is None or t > b:
            b = t

    return (a, b)


def analyze_find_client_ips(records):
    ips = {}

    for r in records:
        ip = r['ip']
        if ip not in ips:
            ips[ip] = Timerange()

        ips[ip].add(r['timestamp'])

    return sorted(ips.items(), key=lambda t: (ip_sort_key(t[0]), t[1]))


def main():
    records = read_acng_logs(LOG_FILE_PATH)

    # Perform analysis
    log_begin, log_end = analyze_find_log_timeframe(records)
    clients = analyze_find_client_ips(records)

    print("\nLog begins %s and ends %s" % (log_begin.isoformat(), log_end))
    print("Client connections:")
    for cip, ctimerange in clients:
        host = cip
        if RESOLVE and not cip.startswith('[INTERNAL'):
            name = socket.getnameinfo((cip, 0), 0)[0]
            host += ' (' + (name if name != cip else '<not found>') + ')'

        print("    %-60s (%5d times between %s and %s)" % (
            host, len(ctimerange), ctimerange.begin(), ctimerange.end()))


#********************************* Exceptions *********************************
class ParseError(Exception):
    pass


if __name__ == '__main__':
    main()
    sys.exit(0)
