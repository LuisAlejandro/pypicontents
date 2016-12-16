
import os
import json

from pipsalabim.core.util import find_files


def main(**kwargs):

    stdlibdict = {}
    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for stdlibfile in find_files(inputdir, '*.json'):
        with open(stdlibfile) as s:
            stdlibdict.update(json.loads(s.read() or '{}'))

    with open(outputfile, 'w') as sw:
        sw.write(json.dumps(stdlibdict, separators=(',', ': '),
                            sort_keys=True, indent=4))
