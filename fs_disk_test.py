import os
import stat

def main():
    root_device = None

    def _work(f):
        nonlocal root_device

        st_buf = os.lstat(f)
        if root_device is None:
            root_device = st_buf.st_dev

        # Don't cross filesystem borders
        if st_buf.st_dev != root_device:
            return

        print(f)

        # Read regular files
        if stat.S_ISREG(st_buf.st_mode):
            with open(f, 'rb') as fhandle:
                while True:
                    buf = fhandle.read(1024 * 1024)
                    if len(buf) == 0:
                        break

        # Recurse on directories
        elif stat.S_ISDIR(st_buf.st_mode):
            for c in list(sorted(os.listdir(f))):
                _work(os.path.join(f, c))


    _work('/')


if __name__ == '__main__':
    main()
