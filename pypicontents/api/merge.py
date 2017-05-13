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
import json

from pipsalabim.core.utils import find_files


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
