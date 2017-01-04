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
