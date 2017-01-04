
import os
import re
import json

from pipsalabim.core.util import find_files


def errors(**kwargs):
    jsondict = {
        'setup': [],
        'api': [],
        'nosetup': [],
        'nosdist': [],
        'nodownloads': []
    }
    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for logfile in find_files(inputdir, '*.log'):
        with open(logfile) as _log:
            content = _log.read()

        if not content:
            continue

        re_setuplist = (r'\[ERROR\]\s*\((.*?)\)\s*\(SETUP\)')
        re_nosetup = (r'\[ERROR\]\s*\((.*?)\)\s*This\s*package\s*has\s*'
                      r'no\s*setup\s*script.')
        re_nosdist = (r'\[ERROR\]\s*\((.*?)\)\s*Could\s*not\s*find\s*a\s*'
                      r'suitable\s*archive\s*to\s*download.')
        re_apilist = (r'\[WARNING\]\s*\((.*?)\)\s*XMLRPC\s*API')
        re_nodownloadslist = (r'\[WARNING\]\s*\((.*?)\)\s*This\s*package')

        setuplist = re.findall(re_setuplist, content)
        nosetup = re.findall(re_nosetup, content)
        nosdist = re.findall(re_nosdist, content)
        apilist = re.findall(re_apilist, content)
        nodownloadslist = re.findall(re_nodownloadslist, content)

        jsondict['setup'].extend(setuplist)
        jsondict['nosetup'].extend(nosetup)
        jsondict['nosdist'].extend(nosdist)
        jsondict['api'].extend(apilist)
        jsondict['nodownloads'].extend(nodownloadslist)

    with open(outputfile, 'w') as e:
        e.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
