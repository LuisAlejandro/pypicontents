import os
import json
import warnings

from sphinx.ext.intersphinx import fetch_inventory
from pipsalabim.api.report import get_modules, get_packages
from pipsalabim.core.util import list_files

from .. import basedir, libdir
from ..core.utils import s


class DummyApp(object):
    def __init__(self, basedir):
        self.srcdir = basedir
        self.warn = warnings.warn
        self.info = lambda *args: []


def stdlib(**kwargs):

    jsondict = {}
    outputfile = os.path.abspath(kwargs.get('outputfile'))
    pyver = kwargs.get('pyver')
    jsondir = os.path.dirname(outputfile)

    if not os.path.isdir(jsondir):
        os.makedirs(jsondir)

    url = 'http://docs.python.org/{0}/objects.inv'.format(pyver)
    inventory = fetch_inventory(DummyApp(basedir), '', url)
    inventorymodules = list(inventory.get('py:module').keys())

    libpackages = get_packages(libdir)
    libmodules = get_modules(libpackages)

    for f in list_files(libdir, '*.py'):
        libmodules.append(os.path.splitext(os.path.basename(f))[0])

    modules = sorted(list(set(inventorymodules + libmodules)))

    jsondict.update({pyver: [s(m) for m in modules]})

    with open(outputfile, 'w') as j:
        j.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
