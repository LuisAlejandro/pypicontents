import os
import re


class fake_distribute_setup(object):
    @staticmethod
    def use_setuptools():
        print "This package tried to install distribute, oh boy."

def dummysetup(*args, **kwargs):
    global setupargs
    setupargs = kwargs

def dummyexit(*args, **kwargs):
    print "This package tried to exit, but i'm smarter than them."

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

