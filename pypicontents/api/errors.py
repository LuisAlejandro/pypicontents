
import os
import re
import json

from pipsalabim.core.util import find_files


def errors(**kwargs):

    jsondict = {'setup': [], 'api': [], 'nosetup': [], 'nosdist': [], 'nodownloads': []}
    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for logfile in find_files(inputdir, '*.log'):
        with open(logfile) as _log:
            content = _log.read()

        if not content:
            continue

        setuplist = re.findall(r'\[ERROR\]\s*\((.*?)\)\s*\(SETUP\)', content)
        nosetup = re.findall(r'\[ERROR\]\s*\((.*?)\)\s*This\s*package\s*has\s*no\s*setup\s*script.', content)
        nosdist = re.findall(r'\[ERROR\]\s*\((.*?)\)\s*Could\s*not\s*find\s*a\s*suitable\s*archive\s*to\s*download.', content)
        apilist = re.findall(r'\[WARNING\]\s*\((.*?)\)\s*XMLRPC\s*API', content)
        nodownloadslist = re.findall(r'\[WARNING\]\s*\((.*?)\)\s*This\s*package', content)

        jsondict['setup'].extend(setuplist)
        jsondict['nosetup'].extend(nosetup)
        jsondict['nosdist'].extend(nosdist)
        jsondict['api'].extend(apilist)
        jsondict['nodownloads'].extend(nodownloadslist)

    with open(outputfile, 'w') as e:
        e.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
