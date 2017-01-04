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

from pipsalabim.core.util import find_files


def stats(**kwargs):

    total = 0
    processed = 0
    updated = 0
    uptodate = 0
    setuperror = 0
    nosdist = 0
    nosetup = 0
    nodownloads = 0
    api = 0
    noproc = 0

    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    re_total = (r'\s*Total\s*number\s*of\s*packages:\s*(\d*)')
    re_processed = (r'\s*No.\s*of\s*processed\s*packages:\s*(\d*)')
    re_updated = (r'\s*No.\s*of\s*updated\s*packages:\s*(\d*)')
    re_uptodate = (r'\s*No.\s*of\s*up-to-date\s*packages:\s*(\d*)')
    re_setup_error = (r'\s*No.\s*of\s*packages\s*unable\s*to'
                      r'\s*read\s*setup:\s*(\d*)')
    re_no_sdist = (r'\s*No.\s*of\s*packages\s*with\s*no\s*'
                   r'source\s*downloads:\s*(\d*)')
    re_no_setup = (r'\s*No.\s*of\s*packages\s*without\s*setup'
                   r'\s*script:\s*(\d*)')
    re_nodownloads = (r'\s*No.\s*of\s*packages\s*without\s*downloads:'
                      r'\s*(\d*)')
    re_api = (r'\s*No.\s*of\s*packages\s*without\s*response\s*from\s*API:'
              r'\s*(\d*)')
    re_noproc = (r'\s*No.\s*of\s*packages\s*that\s*could\s*not\s*be'
                 r'\s*processed:\s*(\d*)')

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
        setuperror += int((re.findall(re_setup_error, content)[0:] + [0])[0])
        nosdist += int((re.findall(re_no_sdist, content)[0:] + [0])[0])
        nosetup += int((re.findall(re_no_setup, content)[0:] + [0])[0])
        nodownloads += int((re.findall(re_nodownloads, content)[0:] + [0])[0])
        api += int((re.findall(re_api, content)[0:] + [0])[0])
        noproc += int((re.findall(re_noproc, content)[0:] + [0])[0])

    with open(outputfile, 'w') as s:
        s.write('Total number of packages: %s\n' % total)
        s.write('\tNo. of processed packages: %s\n' % processed)
        s.write('\t\tNo. of updated packages: %s\n' % updated)
        s.write('\t\tNo. of up-to-date packages: %s\n' % uptodate)
        s.write('\t\tNo. of packages unable to read setup: %s\n' % setuperror)
        s.write('\t\tNo. of packages with no source downloads: %s\n' % nosdist)
        s.write('\t\tNo. of packages without setup script: %s\n' % nosetup)
        s.write('\t\tNo. of packages without downloads: %s\n' % nodownloads)
        s.write('\t\tNo. of packages without response from API: %s\n' % api)
        s.write('\tNo. of packages that could not be processed: %s\n' % noproc)
