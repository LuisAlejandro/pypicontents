# -*- coding: utf-8 -*-

import io

try:
    from __builtin__ import __import__ as _import
except ImportError:
    from builtins import __import__ as _import

from .utils import default_import_level


def false_import(name, globals={}, locals={},
                 fromlist=[], level=default_import_level):

    modules_to_fake = ['distribute_setup', 'Cython.build', 'Cython.Build',
                       'Cython.Distutils', 'pypandoc', 'numpy', 'numpy.distutils',
                       'numpy.random', 'numpy.core.numeric', 'numpy.core', 'ez_setup',
                       'scipy.weave', 'ldap3', 'ldap3.utils.conv', 'ldap3.protocol.rfc4511',
                       'yaml', 'arrayfire', 'django.utils', 'django.conf']

    class ImpostorModule(object):
        def __init__(self, *args, **kwargs):
            pass
        def __repr__(self, *args, **kwargs):
            return ''
        def __call__(self, *args, **kwargs):
            return self
        def __enter__(self, *args, **kwargs):
            return ''
        def __exit__(self, *args, **kwargs):
            pass
        def __setitem__(self, *args, **kwargs):
            pass
        def __getitem__(self, *args, **kwargs):
            return self
        def __setattr__(self, *args, **kwargs):
            pass
        def __getattr__(self, *args, **kwargs):
            return self

    def return_empty_list(*args, **kwargs):
        return []

    def do_nothing(*args, **kwargs):
        pass

    def false_setup(*args, **kwargs):
        global setupargs
        setupargs = {}
        if 'py_modules' in kwargs:
            setupargs.update({'py_modules': kwargs['py_modules']})
        if 'packages' in kwargs:
            setupargs.update({'packages': kwargs['packages']})
        if 'scripts' in kwargs:
            setupargs.update({'scripts': kwargs['scripts']})

    if name in modules_to_fake:
        return ImpostorModule()

    mod = _import(name, globals, locals, fromlist, level)

    if name in ['setuptools', 'distutils.core']:
        mod.setup = false_setup
    if name == 'pip.req':
        mod.parse_requirements = return_empty_list
    if name == 'sys':
        mod.exit = do_nothing
    if name == 'os':
        mod._exit = do_nothing
        mod.system = do_nothing
    return mod

def patchedglobals():
    env = globals()
    env.update({
        '__name__': '__main__',
        '__package__': None,
    })
    env['__builtins__'].update({
        'open': io.open,
        'exit': lambda *args: None,
        '__import__': false_import
    })
    return env
