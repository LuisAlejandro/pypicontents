# -*- coding: utf-8 -*-

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

from .utils import default_import_level, u


if sys.version_info < (3,):
    FileNotFoundError = IOError


def false_import(name, globals={}, locals={},
                 fromlist=[], level=default_import_level):

    banned_impostors = ['antlr3', 'astor', 'autowrap', 'babel',
    'bacpypes', 'BEEMINDER_KEY', 'bibtexparser', 'Bio', 'botocore',
    'bzrlib', 'celerid', 'celery', 'cffi', 'charade', 'circuits', 'click',
    'clint', 'COIN_INSTALL_DIR', 'commons', 'creole', 'Crypto', 'Cython',
    'Cython.Distutils.build_ext', 'cythrust', 'dd', 'distutils2',
    'distutils.command.py', 'DistUtilsExtra', 'django', 'dns', 'docutils',
    'epsilon', '__file__', 'flask', 'foruse', 'gfworks', 'git_revision',
    'google', 'grako', 'graph_db', 'h5config', 'hgtools', 'IDL_DIR',
    'INCLUDEDIR', 'installed_solvers', 'IPython', 'itools', 'java', 'jip',
    'kiwi', 'lib', 'libsovereign', 'llvm', 'LOGNAME', 'mako', 'marshmallow',
    'matplotlib', 'mercurial', 'mytools', 'name', 'ndg', 'networkx', 'nisext',
    'nummodule', 'numpy', 'numpydoc', 'packaging', 'parsimonious', 'paver',
    'pgp', 'pip._vendor.six.moves', 'pip._vendor.six', 'plib', 'ply', 'portage',
    'protorpc', 'psycopg2', 'PWD', 'py2exe', 'pycoin', 'pyfftw', 'pygame', 'pyglet',
    'pygments', 'pykern', 'pymongo', 'PyQt4', 'PyQt5', 'rabird', 'rdflib',
    'reviewboard', 'rimudns', 'salt', 'scipy', 'SDL', 'selenium',
    'setuptools.command.config', 'sflib', 'six', 'sklearn', 'sleipnir.core',
    'sphinx', 'storm', 'stsci', 'subunit', 'SYSTEMDRIVE', 'tiddlywebplugins',
    'torfy.utils', 'tornado', 'trac', 'twisted', 'uliweb', 'utils',
    '__version__', 'werkzeug', 'win32com', 'win_unicode_console', 'wx', 'yormi',
    'org', 'org.python', 'pip._vendor.requests.packages.urllib3.exceptions',
    'pip._vendor.requests.packages.urllib3', 'pip._vendor.requests.packages',
    'pip._vendor.requests', 'autowrap', 'BEEMINDER_KEY', 'Cython.Compiler',
    'Cython.Distutils', '__file__', 'gdbm', 'gfworks.templates', 'jinja2',
    'markdown', 'ndg.httpsclient', 'numpy.distutils', 'pandas',
    'pip._vendor.packaging', 'twisted.python', 'win32com.client']

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

    def return_zero(*args, **kwargs):
        return 0

    def return_empty_str(*args, **kwargs):
        return ''

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
        if name in banned_impostors:
            raise
        mod = ImpostorModule()

    if name == 'distribute_setup':
        mod.use_setuptools = return_zero
    if name in ['setuptools', 'distutils.core']:
        mod.setup = false_setup
        print mod.setup
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
        mod.Popen.stdout = None
        mod.Popen.stderr = None
        mod.Popen.stdin = None
        mod.call = return_zero
        mod.check_output = return_empty_str
    return mod

def false_open(*args, **kwargs):
    try:
        return _open(*args, **kwargs)
    except (IOError, FileNotFoundError) as e:
        args = list(args)
        args[0] = os.devnull
        return _open(*args, **kwargs)

def patchedglobals():
    bi.exit = lambda *args: None
    bi.open = false_open
    bi.__import__ = false_import
    return dict(__name__='__main__', __doc__=None,
                __package__=None, __builtins__=bi)
