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
import re
import sys
import json
import zlib
import codecs

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from pipsalabim.api.report import get_modules, get_packages
from pipsalabim.core.utils import list_files, u

from .. import libdir
from ..core.logger import logger


UTF8StreamReader = codecs.lookup('utf-8')[2]


def read_inventory_v1(f, uri):
    # type: (IO, unicode, Callable) -> Inventory
    f = UTF8StreamReader(f)
    invdata = {}  # type: Inventory
    line = next(f)
    projname = line.rstrip()[11:]
    line = next(f)
    version = line.rstrip()[11:]
    for line in f:
        name, type, location = line.rstrip().split(None, 2)
        location = os.path.join(uri, location)
        # version 1 did not add anchors to the location
        if type == 'mod':
            type = 'py:module'
            location += '#module-' + name
        else:
            type = 'py:' + type
            location += '#' + name
        invdata.setdefault(type, {})[name] = (projname, version, location, '-')
    return invdata


def read_inventory_v2(f, uri, bufsize=16 * 1024):
    # type: (IO, unicode, Callable, int) -> Inventory
    invdata = {}  # type: Inventory
    line = f.readline()
    projname = line.rstrip()[11:].decode('utf-8')
    line = f.readline()
    version = line.rstrip()[11:].decode('utf-8')
    line = f.readline().decode('utf-8')

    if 'zlib' not in line:
        raise ValueError('This is not a gzipped file.')

    def read_chunks():
        # type: () -> Iterator[bytes]
        decompressor = zlib.decompressobj()
        for chunk in iter(lambda: f.read(bufsize), b''):
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def split_lines(iter):
        # type: (Iterator[bytes]) -> Iterator[unicode]
        buf = b''
        for chunk in iter:
            buf += chunk
            lineend = buf.find(b'\n')
            while lineend != -1:
                yield buf[:lineend].decode('utf-8')
                buf = buf[lineend + 1:]
                lineend = buf.find(b'\n')
        assert not buf

    for line in split_lines(read_chunks()):
        # be careful to handle names with embedded spaces correctly
        m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)',
                     line.rstrip())
        if not m:
            continue
        name, type, prio, location, dispname = m.groups()
        if type == 'py:module' and type in invdata and \
                name in invdata[type]:  # due to a bug in 1.1 and below,
                                        # two inventory entries are created
                                        # for Python modules, and the first
                                        # one is correct
            continue
        if location.endswith(u('$')):
            location = location[:-1] + name
        location = os.path.join(uri, location)
        invdata.setdefault(type, {})[name] = (projname, version,
                                              location, dispname)
    return invdata


def read_inventory(f, uri):
    # type: (IO, unicode, Callable, int) -> Inventory
    line = f.readline().rstrip().decode('utf-8')
    if line == '# Sphinx inventory version 1':
        return read_inventory_v1(f, uri)
    elif line == '# Sphinx inventory version 2':
        return read_inventory_v2(f, uri)


def fetch_inventory(uri, inv):
    # type: (Sphinx, unicode, Any) -> Any
    """Fetch, parse and return an intersphinx inventory file."""
    # both *uri* (base URI of the links to generate) and *inv* (actual
    # location of the inventory file) can be local or remote URIs
    try:
        f = urlopen(inv)
    except Exception as e:
        logger.warning('intersphinx inventory %r not fetchable due to '
                       '%s: %s' % (inv, e.__class__.__name__, e))
        return
    try:
        invdata = read_inventory(f, uri)
    except Exception as e:
        logger.warning('intersphinx inventory %r not readable due to '
                       '%s: %s' % (inv, e.__class__.__name__, e))
    else:
        return invdata


def stdlib(**kwargs):

    jsondict = {}
    outputfile = os.path.abspath(kwargs.get('outputfile'))
    pyver = '%s.%s' % (sys.version_info[0], sys.version_info[1])
    jsondir = os.path.dirname(outputfile)

    if not os.path.isdir(jsondir):
        os.makedirs(jsondir)

    inv = 'http://docs.python.org/{0}/objects.inv'.format(pyver)
    uri = 'http://docs.python.org/{0}'.format(pyver)
    inventory = fetch_inventory(uri, inv) or {'py:module': {}}
    inventorymodules = list(inventory.get('py:module').keys())

    libpackages = get_packages(libdir)
    libmodules = get_modules(libpackages)

    for f in list_files(libdir, '*.py'):
        libmodules.append(os.path.splitext(os.path.basename(f))[0])

    modules = sorted(list(set(inventorymodules + libmodules)))

    jsondict.update({pyver: [u(m) for m in modules]})

    with open(outputfile, 'w') as j:
        j.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
