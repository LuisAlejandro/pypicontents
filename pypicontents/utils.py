import os
import re


def pygrep(pattern, dir):
    r = re.compile(pattern)
    for parent, dnames, fnames in os.walk(dir):
        for fname in fnames:
            filename = os.path.join(parent, fname)
            if os.path.isfile(filename):
                with open(filename) as f:
                    for line in f:
                        if r.search(line):
                            yield filename

