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
"""
``pypicontents.api.report`` is a module implementing the report command.

This module contains the logic to examine your source code, extract internal
and external imports, and finally determine which external PyPI packages
you need to install in order to satisfy dependencies.
"""

import os
import glob
import time
import json
import types
import string
import shutil
import tarfile
import zipfile
import traceback
import subprocess
import signal
from resource import RUSAGE_SELF, getrusage
from contextlib import closing

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from pipsalabim.core.utils import chunk_read, chunk_report, u

from .. import pypiurl
from ..core.logger import logger
from ..core.utils import (get_tar_extension, urlesc, filter_package_list,
                          create_file_if_notfound, timeout, human2bytes,
                          translate_letter_range, get_free_memory,
                          get_children_processes)


def execute_wrapper(setuppath):
    errlist = []
    pbs = glob.glob('/usr/bin/python?.?')
    if os.path.isfile(setuppath):
        pkgpath = os.path.dirname(setuppath)
    if os.path.isdir(setuppath):
        pkgpath = setuppath
    storepath = os.path.join(pkgpath, 'setupargs-pypicontents.json')

    for cmd in [(pb, '-m', 'pypicontents.wrapper', setuppath) for pb in pbs]:
        try:
            with timeout(error='Execution of setup.py took too much time.'):
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                stdout = u(stdout).strip('\n').strip()
                stderr = u(stderr).strip('\n').strip()
            if p.poll() is None:
                p.kill()
            if os.path.isfile(storepath):
                with open(storepath) as store:
                    return json.loads(store.read()), ''
        except Exception:
            errlist.append(traceback.format_exc())
        else:
            errlist.append('Execution of {0} failed with the following '
                           'messages:'.format(' '.join(cmd)))
            if stdout:
                errlist.append('[stdout] {0}'.format(stdout))
            if stderr:
                errlist.append('[stderr] {0}'.format(stderr))
            if not stdout and not stderr:
                errlist.append('Unknown reason.')
    return {}, '\n'.join(errlist)


def download_tar(pkgurl, tarpath):
    try:
        with open(tarpath, 'wb') as f:
            f.write(urlopen(url=urlesc(pkgurl), timeout=10).read())
        return True, ''
    except Exception:
        return False, traceback.format_exc()


def get_tar_topdir(tarpath, tarext, extractdir):
    if tarext in ['.zip', '.whl', '.egg']:
        tarmode = 'r'
        compressed = zipfile.ZipFile
        zipfile.ZipFile.list = zipfile.ZipFile.namelist

    elif tarext in ['.tar.gz', '.tgz']:
        tarmode = 'r:gz'
        compressed = tarfile.open
        tarfile.TarFile.list = tarfile.TarFile.getnames

    elif tarext == '.tar.bz2':
        tarmode = 'r:bz2'
        compressed = tarfile.open
        tarfile.TarFile.list = tarfile.TarFile.getnames

    try:
        with timeout(error='Uncompressing took too much time.'):
            with closing(compressed(tarpath, tarmode)) as tar:
                tar.extractall(extractdir)
                tarlist = tar.list()
        if tarext == '.whl':
            return extractdir, ''
        else:
            return tarlist[0].split(os.sep)[0], ''
    except Exception:
        return '', traceback.format_exc()


def get_pkgpath(pkgname, pkgversion, pkgurl, cachedir, extractdir):
    tarname = get_tarname(pkgname, pkgversion, pkgurl)
    tarpath = os.path.join(cachedir, tarname)
    tarext = get_tar_extension(tarpath)

    if not tarext:
        return '', '', ('This package download URL does not point to a'
                        ' valid file: "{0}"'.format(pkgurl))

    if tarext not in ['.whl', '.egg', '.zip', '.tgz', '.tar.gz', '.tar.bz2']:
        return '', tarpath, '"{0}" extension not supported.'.format(tarext)

    if not os.path.isfile(tarpath):
        tardown, errstring = download_tar(pkgurl, tarpath)

        if not tardown:
            return '', tarpath, ('"{0}" file could not be downloaded. See '
                                 'below for details.\n{1}'.format(pkgurl,
                                                                  errstring))

    topdir, errstring = get_tar_topdir(tarpath, tarext, extractdir)

    if not topdir:
        return '', tarpath, ('Could not extract tarball. See below for '
                             'details.\n{0}'.format(errstring))

    if topdir == '.':
        return '', tarpath, 'Unsupported package directory structure.'

    pkgpath = os.path.normpath(os.path.join(extractdir, topdir))

    if os.path.isdir(pkgpath):
        return pkgpath, tarpath, ''
    return '', tarpath, ''


def get_setupargs(pkgname, pkgversion, pkgurls, cachedir, extractdir):
    setupargs = {}
    errlist = []

    for utype in pkgurls:
        if not pkgurls[utype]:
            continue

        pkgpath, tarpath, errstring = get_pkgpath(
            pkgname, pkgversion, pkgurls[utype], cachedir, extractdir)

        if not pkgpath:
            errlist.append(errstring)
            continue

        setuppath = os.path.join(pkgpath, 'setup.py')

        if os.path.isfile(setuppath):
            setupargs, errstring = execute_wrapper(setuppath)
            if setupargs:
                return setupargs, pkgpath, tarpath, ''
            errlist.append(errstring)

        if os.path.isdir(pkgpath):
            setupargs, errstring = execute_wrapper(pkgpath)
            if setupargs:
                return setupargs, pkgpath, tarpath, ''
            errlist.append(errstring)
    return setupargs, pkgpath, tarpath, ''.join(errlist)


def get_tarname(pkgname, pkgversion, pkgurl):
    parsedurl = urlparse(pkgurl)
    if parsedurl.netloc in ['gitlab.com', 'www.gitlab.com'] and \
       os.path.basename(parsedurl.path) == 'archive.tar.gz':
        tarname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)
    elif (parsedurl.netloc in ['github.com', 'www.github.com'] and
          os.path.basename(parsedurl.path) == 'master'):
        tarname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)
    else:
        tarname = os.path.basename(parsedurl.path)
    return tarname


def fix_empty_releases(pkgdata, pkgversion):
    if not pkgdata['releases'][pkgversion] and \
       'download_url' in pkgdata['info'] and \
       pkgdata['info']['download_url'] and \
       pkgdata['info']['download_url'] != 'UNKNOWN':
        _url = urlparse(pkgdata['info']['download_url'])

        if _url.netloc in ['gitlab.com', 'www.gitlab.com']:
            _path = os.path.join(*_url.path.split('/')[:3])
            _path = os.path.join(_path, 'repository', 'archive.tar.gz')
            _tar = urlunparse(('https', 'gitlab.com', _path, '', 'ref=master',
                               ''))
        elif _url.netloc in ['github.com', 'www.github.com']:
            _path = os.path.join(*_url.path.split('/')[:3])
            _path = os.path.join(_path, 'tarball', 'master')
            _tar = urlunparse(('https', 'github.com', _path, '', '', ''))
        else:
            _path = ''
            _tar = pkgdata['info']['download_url']
        pkgdata['releases'][pkgversion] = [{'url': _tar,
                                            'packagetype': 'sdist'}]
    return pkgdata


def get_pkgurls(pkgdata, pkgname, pkgversion):
    try:
        pkgdata = fix_empty_releases(pkgdata, pkgversion)
        pkgrel = pkgdata['releases'][pkgversion]
        sources = list(filter(lambda x: x['packagetype'] == 'sdist', pkgrel))
        whl = list(filter(lambda x: x['packagetype'] == 'bdist_wheel', pkgrel))
        eggs = list(filter(lambda x: x['packagetype'] == 'bdist_egg', pkgrel))
        pkgurls = {'sdist': sources[0]['url'] if sources else '',
                   'bdist_wheel': whl[0]['url'] if whl else '',
                   'bdist_egg': eggs[0]['url'] if eggs else ''}
        return pkgurls, ''
    except Exception:
        return {}, traceback.format_exc()


def get_pkgdata(pkgname):
    try:
        pkgjsonraw = urlopen(url='{0}/pypi/{1}/json'.format(pypiurl, pkgname),
                             timeout=10).read()
        pkgjson = json.loads(pkgjsonraw.decode('utf-8'))
        return {'info': pkgjson['info'],
                'releases': pkgjson['releases']}, ''
    except Exception:
        return {}, traceback.format_exc()


class PyPIParser(HTMLParser):
    def __init__(self):
        if hasattr(types, 'ClassType') and \
           isinstance(HTMLParser, types.ClassType):
            HTMLParser.__init__(self)
        if (hasattr(types, 'TypeType') and
           isinstance(HTMLParser, types.TypeType)) or \
           isinstance(HTMLParser, type):
            super(PyPIParser, self).__init__()
        self.pypilist = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.pypilist.append(attrs[0][1].split(os.sep)[2])


def get_pkglist():
    try:
        pkglistobj = urlopen(url='{0}/simple'.format(pypiurl), timeout=60)
        pkglistraw = chunk_read(pkglistobj, report_hook=chunk_report)
        pypiparser = PyPIParser()
        pypiparser.feed(pkglistraw)
        return pypiparser.pypilist
    except Exception:
        return {}


def get_outputfile_jsondict(outputfile):
    try:
        with open(outputfile, 'r') as f:
            outjsondict = json.loads(f.read() or '{}')
        return outjsondict
    except Exception:
        return {}


def prefill_jsondict(pkglist, jsondict, outjsondict):
    for pkgname in pkglist:
        if pkgname not in jsondict:
            if pkgname in outjsondict:
                jsondict[pkgname] = outjsondict[pkgname]
            else:
                jsondict[pkgname] = {'version': '',
                                     'modules': [],
                                     'cmdline': []}
    return jsondict


def pypi(**kwargs):
    jsondict = {}
    sum_updated = 0
    sum_uptodate = 0
    sum_nodata = 0
    sum_nodown = 0
    sum_noapi = 0
    sum_nourls = 0
    limit_mem_available = 600 * 1024 * 1024
    allowed_range = list(string.ascii_lowercase) + list(map(str, range(0, 10)))
    start_time = time.time()

    logfile = kwargs.get('logfile')
    if logfile:
        logfile = os.path.abspath(logfile)
    outputfile = os.path.abspath(kwargs.get('outputfile'))
    extractdir = os.path.abspath(kwargs.get('extractdir'))
    cachedir = os.path.abspath(kwargs.get('cachedir'))
    limit_mem = kwargs.get('limit_mem')
    limit_log_size = kwargs.get('limit_log_size')
    letter_range = translate_letter_range(kwargs.get('letter_range'))
    limit_time = int(kwargs.get('limit_time'))
    clean = kwargs.get('clean')

    if limit_mem.isdigit():
        limit_mem = '{0}B'.format(limit_mem)

    if limit_log_size.isdigit():
        limit_log_size = '{0}B'.format(limit_log_size)

    limit_mem = human2bytes(limit_mem)
    limit_log_size = human2bytes(limit_log_size)

    if len(set(letter_range) - set(allowed_range)):
        raise RuntimeError('"{0}" not in allowed range.'.format(
            ', '.join(set(letter_range) - set(allowed_range))))

    if not os.path.isdir(extractdir):
        os.makedirs(extractdir)

    if not os.path.isdir(cachedir):
        os.makedirs(cachedir)

    if not os.path.isfile(outputfile):
        create_file_if_notfound(outputfile)

    logger.info('Downloading package list from PyPI ...')
    pkglist = filter_package_list(get_pkglist(), letter_range)

    if not pkglist:
        raise RuntimeError('Couldnt download the PyPI package list.\n'
                           'There was an error stablishing communication '
                           'with {0}'.format(pypiurl))

    outjsondict = get_outputfile_jsondict(outputfile)
    jsondict = prefill_jsondict(pkglist, jsondict, outjsondict)

    for pkgname in sorted(jsondict.keys()):

        elapsed_time = int(time.time() - start_time)
        mem_usage = int(getrusage(RUSAGE_SELF).ru_maxrss * 1024)
        mem_available = int(get_free_memory())

        for chpid in get_children_processes(os.getpid()):
            os.kill(int(chpid), signal.SIGKILL)

        if logfile:
            logsize = int(os.path.getsize(logfile))
        else:
            logsize = 0

        logger.configpkg(pkgname)

        if elapsed_time > limit_time:
            logger.configpkg()
            logger.warning('')
            logger.warning('Processing has taken more than {0} seconds.'
                           ' Interrupting.'.format(limit_time))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        if mem_usage > limit_mem:
            logger.configpkg()
            logger.warning('')
            logger.warning('This process is taking more than {0} MB of memory.'
                           ' Interrupting'.format(limit_mem / (1024 * 1024)))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        if mem_available < limit_mem_available:
            logger.configpkg()
            logger.warning('')
            logger.warning('This machine is running out of memory.'
                           ' Interrupting.')
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        if logsize > limit_log_size:
            logger.configpkg()
            logger.warning('')
            logger.warning(
                'The log is taking more than {0} MB.'
                ' Interrupting.'.format(logsize / (1024 * 1024)))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        pkgdata, errstring = get_pkgdata(pkgname)

        if not pkgdata:
            logger.error('Could not get a response from API for this package. '
                         'See below for details.\n{0}'.format(errstring))
            sum_noapi += 1
            continue

        newversion = pkgdata['info']['version']
        currentversion = jsondict[pkgname]['version']

        if newversion == currentversion:
            logger.info('This package is up to date.')
            sum_uptodate += 1
            continue

        pkgurls, errstring = get_pkgurls(pkgdata, pkgname, newversion)

        if not pkgurls:
            logger.error('Could not get download URLs for this package. '
                         'See below for details.\n{0}'.format(errstring))
            sum_nourls += 1
            continue

        if not (pkgurls['sdist'] + pkgurls['bdist_wheel'] +
                pkgurls['bdist_egg']):
            logger.error('This package does not have downloadable releases.')
            sum_nodown += 1
            continue

        setupargs, pkgpath, tarpath, errstring = get_setupargs(
            pkgname, newversion, pkgurls, cachedir,
            os.path.join(extractdir, pkgname))

        if clean:
            if os.path.isfile(tarpath):
                os.remove(tarpath)
            if os.path.isdir(pkgpath):
                shutil.rmtree(pkgpath)

        if not setupargs:
            logger.error('Could not extract data from this package. '
                         'See below for details.\n{0}'.format(errstring))
            sum_nodata += 1
            continue

        logger.info('Data has been updated for this package.')
        jsondict[pkgname]['version'] = pkgdata['info']['version']
        jsondict[pkgname].update(setupargs)
        sum_updated += 1

    with open(outputfile, 'w') as f:
        f.write(u(json.dumps(jsondict, separators=(',', ': '),
                             sort_keys=True, indent=4)))

    sum_proc = (sum_updated + sum_uptodate + sum_noapi + sum_nourls +
                sum_nodown + sum_nodata)
    sum_not_proc = len(jsondict.keys()) - sum_proc

    logger.configpkg('')
    logger.info('')
    logger.info('')
    logger.info('Total packages: {0}'.format(len(jsondict.keys())))
    logger.info('    Packages processed: {0}'.format(sum_proc))
    logger.info('        Packages updated: {0}'.format(sum_updated))
    logger.info('        Packages up-to-date: {0}'.format(sum_uptodate))
    logger.info('        Packages without response: {0}'.format(sum_noapi))
    logger.info('        Packages without urls: {0}'.format(sum_nourls))
    logger.info('        Packages without downloads: {0}'.format(sum_nodown))
    logger.info('        Packages with data errors: {0}'.format(sum_nodata))
    logger.info('    Packages not processed: {0}'.format(sum_not_proc))
    logger.info('')
    logger.info('')
