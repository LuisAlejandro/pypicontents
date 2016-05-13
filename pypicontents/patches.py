# -*- coding: utf-8 -*-

import os
import codecs
import sys
import setuptools
import distutils

from io import StringIO
from types import ModuleType


class false_module(ModuleType):
    def __getattr__(self, name):
        print(name)


def false_setup(*args, **kwargs):
    global setupargs
    setupargs = kwargs


def false_exit(*args, **kwargs):
    print('[WARNING] This package tried to exit.')


def patchedglobals(setuppath):

    modules_to_patch = ['distribute_setup',
                        'Cython.build',
                        'Cython.Build',
                        'Cython.Distutils',
                        'pypandoc',
                        'numpy',
                        'numpy.distutils',
                        'scipy.weave',
                        'ldap3',
                        'yaml',
                        'arrayfire',
                        '_thread',
                        'django.utils',
                        'pip.req']

    os._exit = false_exit
    sys.exit = false_exit
    setuptools.setup = false_setup
    distutils.core.setup = false_setup

    env = globals()
    env.update({
        '__file__': setuppath,
        '__name__': '__main__',
        '__package__': None,
        'os._exit': os._exit,
        'sys.exit': sys.exit,
        'setuptools.setup': setuptools.setup,
        'distutils.core.setup': distutils.core.setup,
    })

    env['__builtins__'].update({
        'exit': false_exit
    })


    for m in modules_to_patch:
        env[m] = false_module

    return env

