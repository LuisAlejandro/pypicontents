# -*- coding: utf-8 -*-

import os
import codecs
import sys
import setuptools
import distutils

def patchedglobals(setuppath):

    modules_to_patch = ['distribute_setup', 'Cython.build', 'Cython.Build',
                        'Cython.Distutils', 'pypandoc', 'numpy', 'numpy.distutils',
                        'scipy.weave', 'ldap3', 'yaml', 'arrayfire', #'_thread',
                        'django.utils', 'pip.req']

    os._exit = false_exit
    sys.exit = false_exit
    setuptools.setup = false_setup
    distutils.core.setup = false_setup

    env = {
        '__file__': setuppath,
        '__builtins__.open': false_open,
        '__builtins__.exit': false_exit,
        'os._exit': os._exit,
        'sys.exit': sys.exit,
        'setuptools.setup': setuptools.setup,
        'distutils.core.setup': distutils.core.setup,
    }
    #
    # for m in modules_to_patch:
    #     env.update[m] = false_module
    #
    return env


class false_module(object):
    def __getattr__(self, name):
        print(name)


def false_setup(*args, **kwargs):
    setupargs = kwargs


def false_exit(*args, **kwargs):
    print('[WARNING] This package tried to exit.')


def false_open(file, mode='r', buffering=-1, encoding=None, errors=None,
                newline=None, closefd=True, opener=None):
    if not os.path.isfile(file) and (mode == 'r' or mode == 'rb'):
        print('[WARNING] This package tried to open a file that doesn\'t exist.')
        file = '/dev/null'
    return codecs.open(filename=file, mode=mode, encoding=encoding,
                       errors=errors, buffering=buffering)
