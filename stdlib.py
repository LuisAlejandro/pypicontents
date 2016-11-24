import os
import sys
import json
import fnmatch
import pkgutil
import warnings
from distutils import sysconfig
from contextlib import contextmanager

from sphinx.ext.intersphinx import fetch_inventory
from setuptools import find_packages

if sys.version_info < (3,):
    default_import_level = -1
else:
    default_import_level = 0
    unicode = str
    basestring = str

libdir = sysconfig.get_python_lib(standard_lib=True)


def u(x):
    if isinstance(x, unicode):
        return x
    return x.decode('utf-8')


def s(x):
    if isinstance(x, bytes):
        return x
    return x.encode('utf-8')


@contextmanager
def custom_sys_path(new_sys_path):
    """
    Context manager to momentarily change ``sys.path``.

    :param new_sys_path: a list of paths to overwrite ``sys.path``.

    .. versionadded:: 0.1.0
    """
    old_sys_path = sys.path
    sys.path = new_sys_path
    yield
    sys.path = old_sys_path


@contextmanager
def remove_sys_modules(remove):
    """
    Context manager to momentarily remove modules from ``sys.modules``.

    :param remove: a list of modules to remove from ``sys.modules``.

    .. versionadded:: 0.1.0
    """
    old_sys_modules = sys.modules
    for r in remove:
        if r in sys.modules:
            del sys.modules[r]
    yield
    sys.modules = old_sys_modules


def is_valid_path(path):
    """
    Test if ``path`` is a valid python path.

    :param path: a string containing a path.
    :return: ``True`` if ``path`` is a valid python path. ``False``
             otherwise.

    .. versionadded:: 0.1.0
    """
    for component in os.path.normpath(path).split(os.sep):
        if ('.' in component or '-' in component) and \
           component not in ['.', '..']:
            return False
    return True


def list_files(path=None, pattern='*'):
    """
    List files on ``path`` (non-recursively).

    Locate all the files matching the supplied filename pattern in the first
    level of the supplied ``path``. If no pattern is supplied, all files will
    be returned.

    :param path: a string containing a path where the files will be looked for.
    :param pattern: a string containing a regular expression.
    :return: a list of files matching the pattern within the first level of
             path (non-recursive).

    .. versionadded:: 0.1.0
    """
    assert isinstance(path, basestring)
    assert isinstance(pattern, basestring)

    filelist = []
    for f in fnmatch.filter(os.listdir(path), pattern):
        if os.path.isfile(os.path.join(path, f)):
            filelist.append(os.path.join(path, f))
    return filelist


def find_files(path=None, pattern='*'):
    """
    Locate all the files matching the supplied ``pattern`` in ``path``.

    Locate all the files matching the supplied filename pattern in and below
    the supplied root directory. If no pattern is supplied, all files will be
    returned.

    :param path: a string containing a path where the files will be looked for.
    :param pattern: a string containing a regular expression.
    :return: a list of files matching the pattern within path (recursive).

    .. versionadded:: 0.1
    """
    assert isinstance(path, basestring)
    assert isinstance(pattern, basestring)

    filelist = []
    for directory, subdirs, files in os.walk(os.path.normpath(path)):
        for filename in fnmatch.filter(files, pattern):
            if os.path.isfile(os.path.join(directory, filename)):
                filelist.append(os.path.join(directory, filename))
    return filelist


def get_package_dirs(path):
    """
    List directories containing python packages on ``path``.

    :param path: a path pointing to a directory containing python code.
    :return: a list containing directories of packages.

    .. versionadded:: 0.1.0
    """
    package_dirs = []
    for init in find_files(path, '__init__.py'):
        pkgdir = os.path.dirname(init)
        if os.path.commonprefix([pkgdir, path]) == path and \
           is_valid_path(os.path.relpath(pkgdir, path)):
            while True:
                init = os.path.split(init)[0]
                if not os.path.isfile(os.path.join(init, '__init__.py')):
                    break
            if init not in package_dirs:
                package_dirs.append(init)
    return package_dirs


def get_packages(path):
    """
    List packages living in ``path`` with its directory.

    :param path: a path pointing to a directory containing python code.
    :return: a list of tuples containing the name of the package and
             the package directory. For example::

                 [
                    ('package_a', '/path/to/package_a'),
                    ('package_b.module_b', '/path/to/package_b/module_b'),
                    ('package_c.module_c', '/path/to/package_c/module_c')
                 ]

    .. versionadded:: 0.1.0
    """
    packages = []
    package_dirs = get_package_dirs(path)

    for _dir in package_dirs:
        for pkgname in find_packages(_dir):
            try:
                with custom_sys_path([_dir, libdir]):
                    with remove_sys_modules([pkgname]):
                        pkgdir = pkgutil.get_loader(pkgname).filename
            except:
                pkgdir = os.path.join(_dir, os.sep.join(pkgname.split('.')))
            packages.append([pkgname, pkgdir])
    return packages


def get_modules(pkgdata):
    """
    List modules inside packages provided in ``pkgdata``.

    :param pkgdata: a list of tuples containing the name of a package and
                    the directory where its located.
    :return: a list of the modules according to the list of packages
             provided in ``pkgdata``.

    .. versionadded:: 0.1.0
    """
    modules = []

    for pkgname, pkgdir in pkgdata:
        for py in list_files(pkgdir, '*.py'):
            module = os.path.splitext(os.path.basename(py))[0]
            if not module.startswith('__'):
                modname = '.'.join([pkgname, module])
            else:
                modname = pkgname
            modules.append(modname)
    return sorted(list(set(modules)))


class DummyApp(object):
    def __init__(self, basedir):
        self.srcdir = basedir
        self.warn = warnings.warn
        self.info = lambda *args: []


if __name__ == '__main__':

    jsondict = {}
    basedir = os.path.dirname(__file__)
    stdlibver = os.environ.get('STDLIBCONTENTS')
    stdlibdir = os.path.join(basedir, 'stdlib', stdlibver)
    stdlib = os.path.join(stdlibdir, 'stdlib.json')

    if not os.path.isdir(stdlibdir):
        os.makedirs(stdlibdir)

    url = 'http://docs.python.org/%s/objects.inv' % stdlibver
    inventory = fetch_inventory(DummyApp(basedir), '', url)
    inventorymodules = list(inventory.get('py:module').keys())

    libpackages = get_packages(libdir)
    libmodules = get_modules(libpackages)

    for f in list_files(libdir, '*.py'):
        libmodules.append(os.path.splitext(os.path.basename(f))[0])

    modules = sorted(list(set(inventorymodules + libmodules)))

    jsondict.update({stdlibver: [s(m) for m in modules]})

    with open(stdlib, 'w') as s:
        s.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
