import os
import re
import sys
import json
import zlib

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from pipsalabim.api.report import get_modules, get_packages
from pipsalabim.core.util import list_files

from .. import libdir
from ..core.logger import logger
from ..core.utils import s, u


def read_inventory(f, uri, bufsize=16 * 1024):
    # type: (IO, unicode, Callable, int) -> Inventory
    invdata = {}  # type: Inventory
    line = f.readline()
    line = f.readline()
    projname = line.rstrip()[11:].decode('utf-8')
    line = f.readline()
    version = line.rstrip()[11:].decode('utf-8')
    line = f.readline().decode('utf-8')

    if 'zlib' not in line:
        raise ValueError

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


def fetch_inventory(uri, inv):
    # type: (Sphinx, unicode, Any) -> Any
    """Fetch, parse and return an intersphinx inventory file."""
    # both *uri* (base URI of the links to generate) and *inv* (actual
    # location of the inventory file) can be local or remote URIs
    try:
        f = urlopen(inv)
    except Exception as e:
        logger.warning('intersphinx inventory %r not fetchable due to '
                       '%s: %s' % (inv, e.__class__, e))
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
    inventory = fetch_inventory(uri, inv)
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
