# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import pip
import codecs
import setuptools
import distutils

from pip.req import parse_requirements as _parse_requirements


class fake_module(object):
    def __getattr__(self, name):
        def method(*args):
            print('Hola')
        return method

    @staticmethod
    def cythonize():
        return []

    @staticmethod
    def use_setuptools():
        print('[WARNING] This package tried to install distribute.')

def monkeypatch_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

def monkey_setup(*args, **kwargs):
    global setupargs
    setupargs = kwargs

def monkey_exit(*args, **kwargs):
    print('[WARNING] This package tried to exit.')

@monkeypatch_method(pip.req)
def monkey_parse_requirements(*args, **kwargs):
    if 'filename' in kwargs:
        filename = kwargs['filename']
    elif args:
        filename = args[0]

    if 'session' in kwargs:
        session = kwargs['session']
    else:
        session = pip.download.PipSession()
    return _parse_requirements(filename=filename, session=session)

def monkey_open(file, mode='r', buffering=-1, encoding=None, errors=None,
                newline=None, closefd=True, opener=None):
    if not os.path.isfile(file) and (mode == 'r' or mode == 'rb'):
        print('[WARNING] This package tried to open a file that doesn\'t exist.')
        file = '/dev/null'
    return codecs.open(filename=file, mode=mode, encoding=encoding,
                       errors=errors, buffering=buffering)

modules_to_patch = ['distribute_setup', 'Cython.build', 'Cython.Build',
                    'Cython.Distutils', 'pypandoc', 'numpy', 'numpy.distutils',
                    'scipy.weave', 'ldap3', 'yaml', 'arrayfire', '_thread',
                    'django.utils']
for m in modules_to_patch:
    sys.modules[m] = fake_module

open = monkey_open
exit = monkey_exit
os._exit = monkey_exit
sys.exit = monkey_exit
setuptools.setup = monkey_setup
distutils.core.setup = monkey_setup
# pip.req.parse_requirements = monkey_parse_requirements


