
import os
import sys

from pypicontents.patches import patchedglobals
from pypicontents.utils import s

if __name__ == '__main__':
    setuppath = sys.argv[1]
    pkgpath = os.path.dirname(setuppath)

    env = patchedglobals()
    env.update({'__file__': setuppath})

    os.chdir(pkgpath)
    sys.path.append(pkgpath)

    try:
        with open(setuppath) as _sfile:
            exec(compile(s(_sfile.read()), setuppath, 'exec'), env)
    except Exception as e:
        sys.stderr.write(str(e))
