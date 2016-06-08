# -*- coding: utf-8 -*-

import os
import io
import json

try:
    import __builtin__ as bi
    from __builtin__ import __import__ as _import
except ImportError:
    import builtins as bi
    from builtins import __import__ as _import

from .utils import default_import_level, u


def false_import(name, globals={}, locals={},
                 fromlist=[], level=default_import_level):

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
        setupargs = {}
        pkgpath = os.path.dirname(globals['__file__'])
        storepath = os.path.join(pkgpath, 'store.json')

        if 'py_modules' in kwargs:
            setupargs.update({'py_modules': kwargs['py_modules']})
        if 'packages' in kwargs:
            setupargs.update({'packages': kwargs['packages']})
        if 'scripts' in kwargs:
            setupargs.update({'scripts': kwargs['scripts']})

        with open(storepath, 'w') as store:
            store.write(u(json.dumps(setupargs)))

    try:
        mod = _import(name, globals, locals, fromlist, level)
    except ImportError:
        mod = ImpostorModule()

    if name in ['setuptools', 'distutils.core']:
        mod.setup = false_setup
    if name == 'pip.req':
        mod.parse_requirements = return_empty_list
    if name == 'sys':
        mod.exit = do_nothing
    if name == 'os':
        mod._exit = do_nothing
        mod.system = do_nothing
    if name == 'subprocess':
        mod.Popen = ImpostorModule
        mod.Popen.communicate = lambda *args: ('', '')
    return mod

def patchedglobals():
    bi.open = io.open
    bi.exit = lambda *args: None
    bi.__import__ = false_import
    return dict(__name__='__main__', __doc__=None,
                __package__=None, __builtins__=bi)
