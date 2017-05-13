# -*- coding: utf-8 -*-
#
#   This file is part of PyPIContents.
#   Copyright (C) 2016-2017, PyPIContents Developers.
#
#   Please refer to AUTHORS.rst for a complete list of Copyright holders.
#
#   PyPIContents is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyPIContents is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see http://www.gnu.org/licenses.

import os
import sys
import json

try:
    import __builtin__ as bi
except ImportError:
    import builtins as bi

try:
    from __builtin__ import __import__ as _import
    from __builtin__ import open as _open
except ImportError:
    from builtins import __import__ as _import
    from builtins import open as _open

from pipsalabim.core.utils import u

if sys.version_info < (3,):
    default_import_level = -1
    FileNotFoundError = IOError
else:
    default_import_level = 0
    unicode = str
    basestring = str


def false_import(name, globals={}, locals={}, fromlist=[],
                 level=default_import_level):

    class ImpostorModule(object):
        def __init__(self, *args, **kwargs):
            pass

        def __repr__(self, *args, **kwargs):
            return ''

        def __str__(self, *args, **kwargs):
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

        def __len__(self, *args, **kwargs):
            return 0

        def __add__(self, *args, **kwargs):
            return 0

    def false_setup(*args, **kwargs):
        cmdline = []
        setupdir = os.path.dirname(globals['__file__'])
        storepath = os.path.join(setupdir, 'setupargs-pypicontents.json')
        banned_options = ['setup_requires', 'test_requires', 'conda_buildnum',
                          'd2to1', 'distclass', 'email', 'entry_points',
                          'executables', 'home_page', 'include_package_data',
                          'install_requires', 'licesne', 'namespace_packages',
                          'pbr', 'platform', 'use_2to3', 'use_scm_version']

        from distutils.dist import Distribution
        from distutils.command.build_py import build_py
        from pkg_resources import EntryPoint

        for opt in banned_options:
            kwargs.pop(opt, None)

        kwargs.update({'script_name': globals['__file__'],
                       'script_args': []})

        bpy = build_py(Distribution(kwargs))
        bpy.finalize_options()
        _bpy_mods = bpy.find_all_modules()
        _join_mods = ['.'.join([p, m]).strip('.') for p, m, f in _bpy_mods]
        modules = ['.'.join(m.split('.')[:-1])
                   if m.endswith('.__init__') or m.endswith('.__main__')
                   else m for m in _join_mods]

        if 'scripts' in kwargs:
            cmdline.extend([os.path.basename(s) for s in kwargs['scripts']])
        if 'entry_points' in kwargs:
            entrymap = EntryPoint.parse_map(kwargs['entry_points'])
            if 'console_scripts' in entrymap:
                cmdline.extend(entrymap['console_scripts'].keys())

        with open(storepath, 'w') as store:
            store.write(u(json.dumps({'modules': sorted(set(modules)),
                                      'cmdline': sorted(set(cmdline))})))

    try:
        mod = _import(name, globals, locals, fromlist, level)
    except (ImportError, KeyError):
        mod = ImpostorModule()

    if name == 'warnings':
        mod.showwarning = ImpostorModule()
        mod.filterwarnings = lambda *args, **kwargs: False
    if name == 'distribute_setup':
        mod.use_setuptools = lambda *args, **kwargs: 0
    if name in ['setuptools', 'distutils.core']:
        mod.setup = false_setup
    if name == 'pip.req':
        mod.parse_requirements = lambda *args, **kwargs: []
    if name == 'sys':
        mod.exit = lambda *args, **kwargs: False
    if name == 'os':
        mod._exit = lambda *args, **kwargs: False
        mod.system = lambda *args, **kwargs: False
    if name == 'subprocess':
        mod.Popen = ImpostorModule
        mod.Popen.communicate = lambda *args: ('', '')
        mod.Popen.stdout = None
        mod.Popen.stderr = None
        mod.Popen.stdin = None
        mod.call = lambda *args, **kwargs: 0
        mod.check_output = lambda *args, **kwargs: ''
    if name == 'pycvf.management':
        mod = ImpostorModule()
    return mod


def false_open(*args, **kwargs):
    try:
        return _open(*args, **kwargs)
    except (IOError, FileNotFoundError):
        args = list(args)
        args[0] = os.devnull
        return _open(*args, **kwargs)


def patchedglobals():
    bi.exit = lambda *args: None
    bi.open = false_open
    bi.__import__ = false_import
    return dict(__name__='__main__', __doc__=None,
                __package__=None, __builtins__=bi)
