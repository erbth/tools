import subprocess


def download(pkg, dst):
    res = subprocess.run([
            'apt-get', 'download', pkg['Package'] + ':' + pkg['Architecture'] + '=' + pkg['Version']
        ],
        cwd=dst,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    if res.returncode != 0:
        raise DownloadFailed(pkg,
                res.stdout.decode('utf8') + ' ' + res.stderr.decode('utf8'))

    return ''


def gen_deb_filename(pkg):
    def _work_char(c):
        return {
            ':': '%3a'
        }.get(c, c)

    def _work(s):
        return ''.join(_work_char(c) for c in s)

    return pkg['Package'] + '_' + _work(pkg['Version']) + \
            '_' + pkg['Architecture'] + '.deb'


#********************************** Exceptions ********************************
class DownloadFailed(Exception):
    def __init__(self, pkg, msg):
        super().__init__("Failed to download %s:%s=%s: %s" % (
            pkg['Package'], pkg['Architecture'], pkg['Version'], msg))

        self.pkg = pkg
        self.msg = msg
