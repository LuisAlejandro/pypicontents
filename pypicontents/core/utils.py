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
"""
``pypicontents.core.utils`` is a utility module.

This module contains several utilities to process information coming from the
other modules.
"""

import os
import sys
import signal

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
    return [p for l in lr for p in pkglist if p[0].lower() == l]


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
