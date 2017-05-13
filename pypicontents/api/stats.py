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

from pipsalabim.core.utils import find_files


def stats(**kwargs):

    total = 0
    processed = 0
    updated = 0
    uptodate = 0
    nodata = 0
    noapi = 0
    nodown = 0
    noproc = 0

    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    re_total = (r'\s*Total\s*packages:\s*(\d*)')
    re_processed = (r'\s*Packages\s*processed:\s*(\d*)')
    re_updated = (r'\s*Packages\s*updated:\s*(\d*)')
    re_uptodate = (r'\s*Packages\s*up-to-date:\s*(\d*)')
    re_nodata = (r'\s*Packages\s*with\s*data\s*errors:\s*(\d*)')
    re_nodown = (r'\s*Packages\s*without\s*downloads:\s*(\d*)')
    re_noapi = (r'\s*Packages\s*without\s*response:\s*(\d*)')
    re_noproc = (r'\s*Packages\s*not\s*processed:\s*(\d*)')

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for logfile in find_files(inputdir, '*.log'):
        with open(logfile) as _log:
            content = _log.read()

        if not content:
            continue

        total += int((re.findall(re_total, content)[0:] + [0])[0])
        processed += int((re.findall(re_processed, content)[0:] + [0])[0])
        updated += int((re.findall(re_updated, content)[0:] + [0])[0])
        uptodate += int((re.findall(re_uptodate, content)[0:] + [0])[0])
        nodata += int((re.findall(re_nodata, content)[0:] + [0])[0])
        nodown += int((re.findall(re_nodown, content)[0:] + [0])[0])
        noapi += int((re.findall(re_noapi, content)[0:] + [0])[0])
        noproc += int((re.findall(re_noproc, content)[0:] + [0])[0])

    with open(outputfile, 'w') as s:
        s.write('Total packages: {0}\n'.format(total))
        s.write('\tPackages processed: {0}\n'.format(processed))
        s.write('\t\tPackages updated: {0}\n'.format(updated))
        s.write('\t\tPackages up-to-date: {0}\n'.format(uptodate))
        s.write('\t\tPackages with data errors: {0}\n'.format(nodata))
        s.write('\t\tPackages without downloads: {0}\n'.format(nodown))
        s.write('\t\tPackages without response: {0}\n'.format(noapi))
        s.write('\tPackages not processed: {0}\n'.format(noproc))
