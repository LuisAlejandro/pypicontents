# -*- coding: utf-8 -*-

import os
import re
import sys
import signal
import logging
import logging.config

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


def getlogging():

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
            }
        },
        'loggers': {
            'pypicontents': {
                'handlers': ['console'],
                'propagate': False,
                'level': 'INFO'
            }
        }
    })

    return logging.getLogger('pypicontents')


def filter_package_list(pkglist=[], lrange='0-z'):
    if '-' in lrange:
        lrange = [ord(lrange.split('-')[0]), ord(lrange.split('-')[1])+1]
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


def create_empty_json(filename):
    jsonfile = create_file_if_notfound(filename)
    with open(jsonfile, 'w') as f:
        f.write(u('{}'))
    return jsonfile


def create_file_from_setup(setup, filename):
    setupdir = os.path.dirname(setup)
    defilerel = os.path.relpath(filename, setupdir)
    defile = os.path.join(setupdir, defilerel)
    return create_file_if_notfound(defile)


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
