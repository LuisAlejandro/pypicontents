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
import resource
import string
import tarfile
import zipfile
from subprocess import Popen, PIPE

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from pkg_resources import parse_version
from pipsalabim.core.util import chunk_read, chunk_report

from .. import pypiurl
from ..core.logger import logger
from ..core.utils import (get_archive_extension, urlesc, filter_package_list,
                          create_file_if_notfound, u, timeout, human2bytes,
                          translate_letter_range)

pypiserver = ServerProxy('{0}/pypi'.format(pypiurl))


def get_setupargs(pkgurls, cachedir, extractdir):
    setupargs = {}

    for tartype in pkgurls:
        if setupargs:
            break

        if not pkgurls[tartype]:
            continue

        pkgpath = get_pkgpath(pkgurls[tartype], cachedir, extractdir)

        if not pkgpath:
            continue

        if tartype in ['bdist_egg', 'bdist_wheel']:
            try:
                setupargs = execute_wrapper(pkgpath)
            except Exception as e:
                logger.exception(e)
        elif tartype == 'sdist':
            setuppath = os.path.join(pkgpath, 'setup.py')
            if not os.path.isfile(setuppath):
                continue
            try:
                setupargs = execute_wrapper(setuppath)
            except Exception as e:
                logger.exception(e)
    return setupargs


def execute_wrapper(setuppath):
    errstring = '\n'
    pbs = glob.glob('/usr/bin/python?.?')
    pkgpath = os.path.dirname(setuppath)
    storepath = os.path.join(pkgpath, 'setupargs-pypicontents.json')

    for cmd in [(pb, '-m', 'pypicontents.wrapper', setuppath) for pb in pbs]:
        with timeout(error='Execution of setup.py took too much time.'):
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            stdout = stdout.strip('\n').strip()
            stderr = stderr.strip('\n').strip()
        if p.poll() is None:
            p.kill()
        if os.path.isfile(storepath):
            with open(storepath) as store:
                return json.loads(store.read())
        errstring += ('Execution of {0} failed with the following '
                      'messages:\n'.format(' '.join(cmd)))
        if stdout:
            errstring += 'stdout: {0}\n'.format(stdout)
        if stderr:
            errstring += 'stderr: {0}\n'.format(stderr)
        if not stdout and not stderr:
            errstring += 'Unknown reason.'
    logger.error(errstring)
    return {}


def download_tar(pkgurl, tarpath):
    try:
        tarcontent = urlopen(url=urlesc(pkgurl), timeout=10).read()
    except Exception as e:
        logger.exception(e)
        return False
    else:
        with open(tarpath, 'wb') as f:
            f.write(tarcontent)
        return True


def get_tar_filelist(tarpath, tarext, extractdir):
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
    else:
        return False

    try:
        with timeout(error='Uncompressing took too much time.'):
            with compressed(tarpath, tarmode) as tar:
                tar.extractall(extractdir)
                tarlist = tar.list()
    except Exception as e:
        logger.exception(e)
        return False
    else:
        return tarlist


def get_pkgpath(pkgurl, cachedir, extractdir):
    tarpath = os.path.join(cachedir, os.path.basename(pkgurl))
    tarext = get_archive_extension(tarpath)

    if tarext not in ['.whl', '.egg', '.zip', '.tgz', '.tar.gz', '.tar.bz2']:
        return

    if not os.path.isfile(tarpath):
        if not download_tar(pkgurl, tarpath):
            return

    tarlist = get_tar_filelist(tarpath, tarext, extractdir)

    if not tarlist:
        return

    pkgtopdir = tarlist[0].split(os.sep)[0]

    if pkgtopdir == '.':
        return

    pkgpath = os.path.normpath(os.path.join(extractdir, pkgtopdir))

    if os.path.isdir(pkgpath):
        return pkgpath
    return


def fix_url_tarnames(pkgname, pkgversion, pkgurls):
    for tartype in pkgurls:
        parsedurl = urlparse(pkgurls[tartype])
        if parsedurl.netloc in ['gitlab.com', 'www.gitlab.com'] and \
           os.path.basename(parsedurl.path) == 'archive.tar.gz':
            tarname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)
        elif (parsedurl.netloc in ['codeload.github.com'] and
              os.path.basename(parsedurl.path) == 'master'):
            tarname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)
        else:
            tarname = os.path.basename(pkgurls[tartype])
        pkgurls[tartype] = os.path.join(os.path.dirname(pkgurls[tartype]),
                                        tarname)
    return pkgurls


def fix_empty_releases(pkgdata, pkgversion):
    if not pkgdata['releases'][pkgversion] and \
       'download_url' in pkgdata['info'] and \
       pkgdata['info']['download_url'] and \
       pkgdata['info']['download_url'] != 'UNKNOWN':
        _url = urlparse(pkgdata['info']['download_url'])

        if _url.netloc in ['gitlab.com', 'www.gitlab.com']:
            _path = os.path.join(*_url.path.split('/')[:3])
            _path = os.path.join(_path, 'repository', 'archive.tar.gz')
            _tar = urlunparse(('https', 'gitlab.com', _path, '',
                               'ref=master', ''))
        elif _url.netloc in ['github.com', 'www.github.com']:
            _path = os.path.join(*_url.path.split('/')[:3])
            _path = os.path.join(_path, 'legacy.tar.gz', 'master')
            _tar = urlunparse(('https', 'codeload.github.com', _path,
                               '', '', ''))
        else:
            _path = ''
            _tar = pkgdata['info']['download_url']
        pkgdata['releases'][pkgversion] = [{'url': _tar,
                                            'packagetype': 'sdist'}]
    return pkgdata


def get_pkgurls(pkgdata, pkgname, pkgversion):
    pkgdata = fix_empty_releases(pkgdata, pkgversion)
    pkgreleases = pkgdata['releases'][pkgversion]
    sources = filter(lambda x: x['packagetype'] == 'sdist', pkgreleases)
    wheels = filter(lambda x: x['packagetype'] == 'bdist_wheel', pkgreleases)
    eggs = filter(lambda x: x['packagetype'] == 'bdist_egg', pkgreleases)
    pkgurls = {'sdist': sources[0]['url'] if sources else '',
               'bdist_wheel': wheels[0]['url'] if wheels else '',
               'bdist_egg': eggs[0]['url'] if eggs else ''}
    return fix_url_tarnames(pkgname, pkgversion, pkgurls)


def get_pkgdata(pkgname):
    try:
        pkgjsonraw = urlopen(url='{0}/pypi/{1}/json'.format(pypiurl, pkgname),
                             timeout=10).read()
        pkgjson = json.loads(pkgjsonraw.decode('utf-8'))
    except Exception as e:
        logger.exception(e)
    else:
        return {'info': pkgjson['info'],
                'releases': pkgjson['releases']}

    try:
        pypireleases = pypiserver.package_releases(pkgname)
        pkgreleases = [parse_version(v) for v in pypireleases]
        if not pkgreleases:
            return {}
        pkgversion = str(sorted(pkgreleases)[-1])
        pkgurls = pypiserver.release_urls(pkgname, pkgversion)
    except Exception as e:
        logger.exception(e)
    else:
        return {'info': {'version': pkgversion},
                'releases': {pkgversion: pkgurls}}
    return {}


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
            self.pypilist.append(attrs[0][1])


def get_pkglist():
    logger.info('Downloading package list from PyPI ...')

    try:
        pkglistobj = urlopen(url='{0}/simple'.format(pypiurl), timeout=60)
        pkglistraw = chunk_read(pkglistobj, report_hook=chunk_report)
        pypiparser = PyPIParser()
        pypiparser.feed(pkglistraw)
        pkglist = pypiparser.pypilist
    except Exception as e:
        logger.exception(e)
    else:
        return pkglist

    try:
        pkglist = pypiserver.list_packages()
    except Exception as e:
        logger.exception(e)
    else:
        return pkglist
    return []


def pypi(**kwargs):

    jsondict = {}
    sum_updated = 0
    sum_uptodate = 0
    sum_nodata = 0
    sum_nodown = 0
    sum_noapi = 0
    allowed_range = list(string.ascii_lowercase) + map(str, range(0, 10))
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

    for pkgname in filter_package_list(get_pkglist(), letter_range):
        if pkgname not in jsondict:
            try:
                with open(outputfile, 'r') as f:
                    outjsondict = json.loads(f.read() or '{}')
            except Exception:
                pass
            else:
                if pkgname in outjsondict:
                    jsondict[pkgname] = outjsondict[pkgname]

        if pkgname not in jsondict:
            jsondict[pkgname] = {'version': '',
                                 'modules': [],
                                 'cmdline': []}

    for pkgname in sorted(jsondict.keys()):

        elapsed_time = int(time.time() - start_time)
        mem_usage = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

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

        if logsize > limit_log_size:
            logger.configpkg()
            logger.warning('')
            logger.warning(
                'The log is taking more than {0} MB.'
                ' Interrupting.'.format(logsize / (1024 * 1024)))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        pkgdata = get_pkgdata(pkgname)

        if not pkgdata:
            logger.error('Could not get a response from API for this package.')
            sum_noapi += 1
            continue

        if jsondict[pkgname]['version'] == pkgdata['info']['version']:
            logger.info('This package is up to date.')
            sum_uptodate += 1
            continue

        pkgurls = get_pkgurls(pkgdata, pkgname, pkgdata['info']['version'])

        if not (pkgurls['sdist'] + pkgurls['bdist_wheel'] +
                pkgurls['bdist_egg']):
            logger.error('This package does not have downloadable releases.')
            sum_nodown += 1
            continue

        setupargs = get_setupargs(pkgurls, cachedir, extractdir)

        if not setupargs:
            logger.error('Could not extract data from this package.')
            sum_nodata += 1
            continue

        logger.info('Data has been updated for this package.')
        jsondict[pkgname]['version'] = pkgdata['info']['version']
        jsondict[pkgname].update(setupargs)
        sum_updated += 1

    with open(outputfile, 'w') as f:
        f.write(u(json.dumps(jsondict, separators=(',', ': '),
                             sort_keys=True, indent=4)))

    sum_processed = (sum_updated + sum_uptodate + sum_nodata +
                     sum_nodown + sum_noapi)
    sum_not_processed = len(jsondict.keys()) - sum_processed

    logger.configpkg('')
    logger.info('')
    logger.info('')
    logger.info('Total packages: {0}'.format(len(jsondict.keys())))
    logger.info('    Packages processed: {0}'.format(sum_processed))
    logger.info('        Packages updated: {0}'.format(sum_updated))
    logger.info('        Packages up-to-date: {0}'.format(sum_uptodate))
    logger.info('        Packages with data errors: {0}'.format(sum_nodata))
    logger.info('        Packages without downloads: {0}'.format(sum_nodown))
    logger.info('        Packages without response: {0}'.format(sum_noapi))
    logger.info('    Packages not processed: {0}'.format(sum_not_processed))
    logger.info('')
    logger.info('')
