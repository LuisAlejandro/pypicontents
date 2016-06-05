
if __name__ == '__main__':

    import os
    import sys
    import errno

    from pypicontents.patches import patchedglobals
    from pypicontents.utils import create_file_from_setup, s

    setuppath = sys.argv[1]
    pkgpath = os.path.dirname(setuppath)

    env = patchedglobals()
    env.update({'__file__': setuppath})

    os.chdir(pkgpath)
    sys.path.append(pkgpath)

    while True:
        try:
            with open(setuppath) as setup:
                exec(compile(s(setup.read()), setuppath, 'exec'), env)
        except BaseException as e:
            if (type(e) == IOError or type(e) == OSError or
                type(e) == FileNotFoundError and e.errno == errno.ENOENT
                and e.filename):
                create_file_from_setup(setuppath, e.filename)
            else:
                print(e)
                break
        else:
            print(env['setupargs'])
            break

