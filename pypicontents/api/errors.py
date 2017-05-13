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

from pipsalabim.core.utils import find_files


def errors(**kwargs):
    jsondict = {
        'nodata': [],
        'nodown': [],
        'noapi': []
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

        re_nodata = (r'\[ERROR\]\s*\((.*?)\)\s*Could\s*not\s*extract\s*'
                     r'data\s*from\s*this\s*package.')
        re_nodown = (r'\[ERROR\]\s*\((.*?)\)\s*This\s*package\s*'
                     r'does\s*not\s*have\s*downloadable\s*releases\.')
        re_noapi = (r'\[ERROR\]\s*\((.*?)\)\s*Could\s*not\s*get\s*a\s*'
                    r'response\s*from\s*API\s*for\s*this\s*package\.')

        nodata = re.findall(re_nodata, content)
        noapi = re.findall(re_noapi, content)
        nodown = re.findall(re_nodown, content)

        jsondict['nodata'].extend(nodata)
        jsondict['noapi'].extend(noapi)
        jsondict['nodown'].extend(nodown)

    with open(outputfile, 'w') as e:
        e.write(json.dumps(jsondict, separators=(',', ': '),
                           sort_keys=True, indent=4))
