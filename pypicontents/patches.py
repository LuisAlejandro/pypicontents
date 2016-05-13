# -*- coding: utf-8 -*-

import os
import sys
import imp


def false_import(name, globals=None, locals=None, fromlist=None, level=None):
    class false_module(object):
        def __init__(self, *args, **kwargs):
            print args, kwargs, 'init'
        def __dict__(self, *args, **kwargs):
            print args, kwargs, 'dict'
        def __call__(self, *args, **kwargs):
            print args, kwargs, 'call'
        def __getattr__(self, name):
            def method(*args, **kwargs):
                print args, kwargs, 'getattr'
            return method

    def false_setup(*args, **kwargs):
        global setupargs
        setupargs = kwargs

    def false_find_module(name):
        try:
            fp, pathname, description = imp.find_module(name)
        except ImportError:
            return false_module
        else:
            return imp.load_module(name, fp, pathname, description)

    if name == 'setuptools' or name == 'distutils.core':
        if 'setup' in fromlist:
            mod = false_find_module(name)
            mod.setup = false_setup
            return mod

    elif name in sys.modules:
        return sys.modules[name]
    else:
        return false_find_module(name)


def patchedglobals(setuppath):

    env = globals()
    env.update({
        '__file__': setuppath,
        '__name__': '__main__',
        '__package__': None,
    })

    env['__builtins__'].update({
        '__import__': false_import
    })

    return env

