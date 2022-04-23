# -*- coding: utf-8 -*-
#
# Please refer to AUTHORS.rst for a complete list of Copyright holders.
# Copyright (C) 2016-2022, PyPIContents Developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
``pypicontents.core.utils`` is a utility module.

This module contains several utilities to process information coming from the
other modules.
"""

import os
import sys
import signal
import fnmatch
import pkgutil
from contextlib import contextmanager
from urllib.parse import urlparse, urlunparse, quote

from setuptools import find_packages

from .. import libdir

default_import_level = 0


def get_free_memory():
    with open('/proc/meminfo', 'r') as memory:
        free = 0
        for mem in memory:
            if str(mem.split()[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free += int(mem.split()[1])
    return free * 1024


def get_children_processes(parent_pid):
    chfile = '/proc/{0}/task/{1}/children'.format(parent_pid, parent_pid)
    with open(chfile, 'r') as children:
        return children.read().strip('\n').strip().split()


class timeout(object):
    def __init__(self, sec=20, error='Operation timed out.'):
        self.sec = sec
        self.error = error

    def handle_timeout(self, signum, frame):
        raise RuntimeError(self.error)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.sec)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


def translate_letter_range(lr='0-z'):
    if '-' in lr:
        lr = [ord(lr.split('-')[0]), ord(lr.split('-')[1]) + 1]
        lr = [chr(i) for i in range(*lr) if 47 < i < 58 or 96 < i < 123]
    elif ',' in lr:
        lr = lr.lower().split(',')
    else:
        lr = [lr.lower()]
    return lr


def filter_package_list(pkglist, lr):
    return [p for lst in lr for p in pkglist if p[0].lower() == lst]


def create_file_if_notfound(filename):
    dedir = os.path.dirname(os.path.abspath(filename))
    if not os.path.isdir(dedir):
        os.makedirs(dedir)
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            f.write('')
    return filename


def urlesc(url):
    parts = urlparse(url)
    return urlunparse(parts[:2] + (quote(parts[2]),) + parts[3:])


def get_tar_extension(path):
    extensions = []
    root, ext = os.path.splitext(path)

    while ext:
        extensions.append(ext)
        if ext in ['.tar', '.zip', '.tgz', '.whl', '.egg']:
            break
        root, ext = os.path.splitext(root)

    return ''.join(extensions[::-1])


def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    SYMBOLS = {
        'customary': ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
        'customary_ext': ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta',
                          'exa', 'zetta', 'iotta'),
        'iec': ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
        'iec_ext': ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                    'zebi', 'yobi')
    }
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]: 1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i + 1) * 10
    return int(num * prefix[letter])


def u(u_string):
    """
    Convert a string to unicode working on both python 2 and 3.

    :param u_string: a string to convert to unicode.

    .. versionadded:: 0.1.5
    """
    if isinstance(u_string, str):
        return u_string
    return u_string.decode('utf-8')


def s(s_string):
    """
    Convert a byte stream to string working on both python 2 and 3.

    :param s_string: a byte stream to convert to string.

    .. versionadded:: 0.1.5
    """
    if isinstance(s_string, bytes):
        return s_string
    return s_string.encode('utf-8')


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
    assert isinstance(path, str)
    assert isinstance(pattern, str)

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
    assert isinstance(path, str)
    assert isinstance(pattern, str)

    filelist = []
    for directory, subdirs, files in os.walk(os.path.normpath(path)):
        for filename in fnmatch.filter(files, pattern):
            if os.path.isfile(os.path.join(directory, filename)):
                filelist.append(os.path.join(directory, filename))
    return filelist


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


def chunk_report(downloaded, total):
    """
    Print the progress of a download.

    :param downloaded: an integer representing the size (in bytes) of data
                       downloaded so far.
    :param total: an integer representing the total size (in bytes) of data
                  that needs to be downloaded.

    .. versionadded:: 0.1.0
    """
    percent = round((float(downloaded) / total) * 100, 2)
    sys.stdout.write(('Downloaded {0:0.0f} of {1:0.0f} kB '
                      '({2:0.0f}%)\r').format(downloaded / 1024,
                                              total / 1024, percent))
    if downloaded >= total:
        sys.stdout.write('\n\n')


def chunk_read(response, chunk_size=8192, report_hook=None):
    """
    Download a file by chunks.

    :param response: a file object as returned by ``urlopen``.
    :param chunk_size: an integer representing the size of the chunks to be
                       downloaded at a time.
    :param report_hook: a function to report the progress of the download.
    :return: a blob containing the downloaded file.

    .. versionadded:: 0.1.0
    """
    data = u('')
    downloaded = 0
    total = int(response.info().get('Content-Length').strip())

    while True:
        chunk = response.read(chunk_size)

        if not chunk:
            break

        data += u(chunk)
        downloaded += len(chunk)

        if report_hook:
            report_hook(downloaded, total)

    return data


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
            except Exception:
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
