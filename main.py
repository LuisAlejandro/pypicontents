
import os
import sys
import errno

from pypicontents.process import process
from pypicontents.patches import patchedglobals
from pypicontents.utils import create_file_from_setup, s, u

if __name__ == '__main__':

    if len(sys.argv) > 1:
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
                if type(e) == IOError or type(e) == OSError:
                    if hasattr(e, 'errno') and hasattr(e, 'filename'):
                        if e.errno == errno.ENOENT:
                            create_file_from_setup(setuppath, e.filename)
                else:
                    sys.stderr.write(str(e))
                    break
            else:
                break
    else:
        try:
            process(os.environ.get('PYPICONTENTSRANGE', '0-z'))
        except KeyboardInterrupt:
            sys.exit('Execution interrupted by user.')
