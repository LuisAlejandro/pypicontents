
import os
import json

from pipsalabim.core.util import find_files


def merge(**kwargs):

    mergedict = {}
    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for mergefile in find_files(inputdir, '*.json'):
        with open(mergefile) as s:
            mergedict.update(json.loads(s.read() or '{}'))

    with open(outputfile, 'w') as sw:
        sw.write(json.dumps(mergedict, separators=(',', ': '),
                            sort_keys=True, indent=4))
