
import os
import json

from pipsalabim.core.util import find_files


def main(**kwargs):

    pypidict = {}
    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for pypifile in find_files(inputdir, '*.json'):
        with open(pypifile) as p:
            pypidict.update(json.loads(p.read() or '{}'))

    with open(outputfile, 'w') as pw:
        pw.write(json.dumps(pypidict, separators=(',', ': '),
                            sort_keys=True, indent=4))
