
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
    notprocessed = 0

    inputdir = os.path.abspath(kwargs.get('inputdir'))
    outputfile = os.path.abspath(kwargs.get('outputfile'))

    re_total = r'\s*Total\s*number\s*of\s*packages:\s*(\d*)'
    re_processed = r'\s*Number\s*of\s*processed\s*packages:\s*(\d*)'
    re_updated = r'\s*Number\s*of\s*updated\s*packages:\s*(\d*)'
    re_uptodate = r'\s*Number\s*of\s*up-to-date\s*packages:\s*(\d*)'
    re_setup_error = r'\s*Number\s*of\s*packages\s*unable\s*to\s*read\s*setup:\s*(\d*)'
    re_no_sdist = r'\s*Number\s*of\s*packages\s*with\s*no\s*source\s*downloads:\s*(\d*)'
    re_no_setup = r'\s*Number\s*of\s*packages\s*without\s*setup\s*script:\s*(\d*)'
    re_nodownloads = (r'\s*Number\s*of\s*packages\s*without\s*downloads:'
                      r'\s*(\d*)')
    re_api = (r'\s*Number\s*of\s*packages\s*without\s*response\s*from\s*API:'
              r'\s*(\d*)')
    re_notprocessed = (r'\s*Number\s*of\s*packages\s*that\s*could\s*not\s*be'
                       r'\s*processed:\s*(\d*)')

    if not os.path.isdir(inputdir):
        os.makedirs(inputdir)

    for logfile in find_files(inputdir, '*.log'):
        with open(logfile) as _log:
            content = _log.read()

        if not content:
            continue

        total += int((re.findall(re_total, content)[0:]+[0])[0])
        processed += int((re.findall(re_processed, content)[0:]+[0])[0])
        updated += int((re.findall(re_updated, content)[0:]+[0])[0])
        uptodate += int((re.findall(re_uptodate, content)[0:]+[0])[0])
        setuperror += int((re.findall(re_setup_error, content)[0:]+[0])[0])
        nosdist += int((re.findall(re_no_sdist, content)[0:]+[0])[0])
        nosetup += int((re.findall(re_no_setup, content)[0:]+[0])[0])
        nodownloads += int((re.findall(re_nodownloads, content)[0:]+[0])[0])
        api += int((re.findall(re_api, content)[0:]+[0])[0])
        notprocessed += int((re.findall(re_notprocessed, content)[0:]+[0])[0])

    with open(outputfile, 'w') as s:
        s.write('Total number of packages: %s\n' % total)
        s.write('    Number of processed packages: %s\n' % processed)
        s.write('        Number of updated packages: %s\n' % updated)
        s.write('        Number of up-to-date packages: %s\n' % uptodate)
        s.write('        Number of packages unable to read setup: %s\n' % setuperror)
        s.write('        Number of packages with no source downloads: %s\n' % nosdist)
        s.write('        Number of packages without setup script: %s\n' % nosetup)
        s.write('        Number of packages without downloads: %s\n' % nodownloads)
        s.write('        Number of packages without response from API: %s\n' % api)
        s.write('    Number of packages that could not be processed: %s\n' % notprocessed)
