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
            print 'Hola'
        return method

    @staticmethod
    def cythonize():
        return []

    @staticmethod
    def use_setuptools():
        print '[WARNING] This package tried to install distribute.'

def monkey_setup(*args, **kwargs):
    global setupargs
    setupargs = kwargs

def monkey_exit(*args, **kwargs):
    print "[WARNING] This package tried to exit."

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
    print 'monkey_open'
    if not os.path.isfile(file):
        print "[WARNING] This package tried to open a file that doesn't exist."
        file = '/dev/null'
    return codecs.open(filename=file, mode=mode, encoding=encoding,
                       errors=errors, buffering=buffering)

def setup_patches():
    modules_to_patch = ['distribute_setup', 'Cython.build', 'Cython.Build',
                        'Cython.Distutils', 'pypandoc', 'numpy', 'numpy.distutils',
                        'scipy.weave', 'ldap3', 'yaml', 'arrayfire', '_thread',
                        'django.utils']
    methods_to_patch = {
        'open': monkey_open,
        'exit': monkey_exit,
        'os._exit': monkey_exit,
        'sys.exit': monkey_exit,
        'setuptools.setup': monkey_setup,
        'distutils.core.setup': monkey_setup,
        'pip.req.parse_requirements': monkey_parse_requirements
    }

    for m in modules_to_patch:
        sys.modules[m] = fake_module

    for k, v in methods_to_patch.items():
        exec('%s = %s' % (k, v.__name__))

    return methods_to_patch

