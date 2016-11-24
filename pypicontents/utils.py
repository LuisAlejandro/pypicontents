# -*- coding: utf-8 -*-

import os
import sys
import signal
import fnmatch
import logging
import logging.config
from contextlib import contextmanager

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

if sys.version_info < (3,):
    default_import_level = -1
else:
    default_import_level = 0
    unicode = str
    basestring = str


def u(x):
    if isinstance(x, unicode):
        return x
    return x.decode('utf-8')


def s(x):
    if isinstance(x, bytes):
        return x
    return x.encode('utf-8')


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


def getlogging(logfile):

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '[%(levelname)s] %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'standard'
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': logfile,
                'formatter': 'standard'
            }
        },
        'loggers': {
            'pypicontents': {
                'handlers': ['console', 'file'],
                'propagate': False,
                'level': 'INFO'
            }
        }
    })

    return logging.getLogger('pypicontents')


def filter_package_list(pkglist=[], lrange='0-z'):
    if '-' in lrange:
        lrange = [ord(lrange.split('-')[0]), ord(lrange.split('-')[1]) + 1]
        lrange = [chr(i) for i in range(*lrange) if 47 < i < 58 or 96 < i < 123]
    elif ',' in lrange:
        lrange = lrange.lower().split(',')
    else:
        lrange = [lrange.lower()]
    return [p for l in lrange for p in pkglist if p.lower().startswith(l)]


def create_file_if_notfound(filename):
    dedir = os.path.dirname(filename)
    if not os.path.isdir(dedir):
        os.makedirs(dedir)
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            os.utime(filename, None)
    return filename


def urlesc(url):
    parts = urlparse(url)
    return urlunparse(parts[:2] + (quote(parts[2]),) + parts[3:])


def get_archive_extension(path):
    extensions = []
    root, ext = os.path.splitext(path)

    while ext:
        extensions.append(ext)
        if ext == '.tar' or ext == '.zip' or ext == '.tgz':
            break
        root, ext = os.path.splitext(root)

    return ''.join(extensions[::-1])


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
