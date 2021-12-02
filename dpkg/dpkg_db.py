import os
import re


AVAILABLE_KEYS = {
    'Package',
    'Status',
    'Priority',
    'Section',
    'Source',
    'Installed-Size',
    'Maintainer',
    'Homepage',
    'Built-Using',
    'Architecture',
    'Multi-Arch',
    'Version',
    'Essential',
    'Important',
    'Replaces',
    'Recommends',
    'Suggests',
    'Enhances',
    'Pre-Depends',
    'Depends',
    'Breaks',
    'Conflicts',
    'Provides',
    'Npp-Applications',
    'Npp-Mimetype',
    'Npp-Name',
    'Cnf-Priority-Bonus',
    'Python-Version',
    'Ruby-Versions',
    'Cnf-Extra-Commands',
    'Conffiles',
    'Efi-Vendor',
    'Gstreamer-Decoders',
    'Gstreamer-Encoders',
    'Gstreamer-Elements',
    'Gstreamer-Uri-Sinks',
    'Gstreamer-Uri-Sources',
    'Gstreamer-Version',
    'Build-Ids',
    'Config-Version',
    'Postgresql-Catversion',
    'Auto-Built-Package',
    'Description',
    'License',
    'Vendor',
    'Cnf-Visible-Pkgname',
    'Protected',
    'Lua-Versions',
}

REQUIRED_KEYS = {
    'Package',
    'Status',
    'Maintainer',
    'Architecture',
    'Version'
}


def gen_pkg_key(pkg):
    return (pkg['Package'], pkg['Architecture'])

class DPKGDB:
    def __init__(self, path):
        self._path = path
        self._status = None

    def read_status(self):
        """
        Read status
        """
        status_path = os.path.join(self._path, 'status')

        self._status = {}
        cur_pkg = None
        last_kw = None
        lineno = 0

        with open(status_path, 'r', encoding='utf8') as f:
            for line in f:
                line = line.rstrip('\n')
                lineno += 1

                # Continued lines
                if line.startswith(' '):
                    if not last_kw:
                        raise InvalidLine(status_path, lineno, "Expected keyword before continued line")

                    cur_pkg[last_kw] += "\n" + line[1:]

                # End of entry
                elif not line:
                    if not cur_pkg:
                        raise InvalidLine(status_path, lineno, "Expected record")

                    k = gen_pkg_key(cur_pkg)
                    if k in self._status:
                        raise InvalidLine(status_path, lineno, "Duplicate package record")

                    # Ensure that required keys are present
                    for rk in REQUIRED_KEYS:
                        if rk not in cur_pkg:
                            raise InvalidLine(status_path, lineno, "Required key '%s' missing" % rk)

                    self._status[k] = cur_pkg
                    cur_pkg = None
                    last_kw = None

                # Regular kv-pair
                else:
                    if cur_pkg is None:
                        cur_pkg = {}

                    m = re.fullmatch(r'([A-Za-z-]+):(?:\s+(\S.*)?)?', line)
                    if not m:
                        raise InvalidLine(status_path, lineno, "Expected k: v")

                    if m[1] not in AVAILABLE_KEYS:
                        raise InvalidLine(status_path, lineno, "Invalid key: '%s'" % m[1])

                    last_kw = m[1]
                    cur_pkg[m[1]] = m[2] or ''


    def __iter__(self):
        for k in sorted(self._status):
            yield(self._status[k])


#********************************** Exceptions ********************************
class InvalidLine(Exception):
    def __init__(self, filename, lineno, msg='?'):
        super().__init__("Invalid line in %s:%d: %s" % (filename, lineno, msg))
