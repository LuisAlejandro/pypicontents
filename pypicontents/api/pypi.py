# -*- coding: utf-8 -*-
#
#   This file is part of PyPIContents.
#   Copyright (C) 2016, PyPIContents Developers.
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
import resource
import string
import shutil
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

from pkg_resources import parse_version
from pipsalabim.api.report import get_modules, get_packages

from .. import extractdir, cachedir, basedir, wrapper, pypiapiend
from ..core.logger import logger
from ..core.utils import (get_archive_extension, urlesc, filter_package_list,
                          create_file_if_notfound, u, timeout, human2bytes,
                          translate_letter_range)

pypiserver = ServerProxy(pypiapiend)


def execute_setup(wrapper, setuppath, pkgname):
    errlist = []
    pybins = glob.glob('/usr/bin/python?.?')
    pkgpath = os.path.dirname(setuppath)
    storepath = os.path.join(pkgpath, 'store.json')

    for cmd in [(pybin, wrapper, setuppath) for pybin in pybins]:
        try:
            with timeout(error='Execution of setup.py took too much time.'):
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
        except Exception:
            if p.poll() is None:
                p.kill()
            raise
        if os.path.isfile(storepath):
            with open(storepath) as store:
                return json.loads(store.read())
        if not stderr:
            stderr = 'Failed for unknown reason.'
        errlist.append('({0}) {1}'.format(cmd[0], stderr))
    raise RuntimeError(' '.join(errlist))


def download_archive(logger, pkgname, arurl, arpath):
    tries = 0
    while tries < 5:
        tries += 1
        try:
            ardownobj = urlopen(url=urlesc(arurl), timeout=10).read()
        except Exception as e:
            logger.warning('Download error: {0} (Try: {1})'.format(e, tries))
        else:
            with open(arpath, 'wb') as f:
                f.write(ardownobj)
            return True
    else:
        return False


def get_archive_filelist(logger, pkgname, arname, arpath, arext, extractdir):
    if arext == '.zip':
        armode = 'r'
        compressed = zipfile.ZipFile
        zipfile.ZipFile.list = zipfile.ZipFile.namelist
    elif (arext == '.tar.gz' or arext == '.tgz' or
          arext == '.tar.bz2'):
        armode = 'r:gz'
        compressed = tarfile.open
        tarfile.TarFile.list = tarfile.TarFile.getnames
        if arext == '.tar.bz2':
            armode = 'r:bz2'

    try:
        with timeout(error='Uncompressing took too much time.'):
            with compressed(arpath, armode) as archive:
                archive.extractall(extractdir)
                arlist = archive.list()
    except Exception as e:
        logger.error('{0}: {1}'.format(type(e).__name__, e))
        return False
    else:
        return arlist


def get_setuppath(logger, pkgname, pkgversion, pkgdownloads):
    setuppath = None

    for pkgtar in pkgdownloads:

        if pkgtar['packagetype'] not in ['sdist', 'bdist_egg']:
            continue

        arurl = pkgtar['url']
        parurl = urlparse(arurl)

        if parurl.netloc in ['gitlab.com', 'www.gitlab.com'] and \
           os.path.basename(parurl.path) == 'archive.tar.gz':
            arname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)

        elif parurl.netloc in ['codeload.github.com'] and \
             os.path.basename(parurl.path) == 'master':
            arname = '{0}-{1}.tar.gz'.format(pkgname, pkgversion)

        else:
            arname = os.path.basename(arurl)

        arpath = os.path.join(cachedir, arname)
        arext = get_archive_extension(arpath)

        if arext not in ['.zip', '.tgz', '.tar.gz', '.tar.bz2']:
            continue

        if not os.path.isfile(arpath):
            if not download_archive(logger, pkgname, arurl, arpath):
                logger.warning('There was an error downloading this package.')
                continue

        arlist = get_archive_filelist(logger, pkgname, arname, arpath, arext,
                                      extractdir)
        if not arlist:
            logger.warning('There was an error extracting this package.')
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))
            continue

        pkgtopdir = arlist[0].split(os.sep)[0]

        if pkgtopdir == '.':
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))
            continue

        pkgpath = os.path.normpath(os.path.join(extractdir, pkgtopdir))
        setuppath = os.path.join(pkgpath, 'setup.py')

        if os.path.isfile(setuppath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))
            break

        pkgpath = extractdir
        setuppath = os.path.join(pkgpath, 'setup.py')

        if os.path.isfile(setuppath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))
            break

        if os.path.isfile(arpath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))

        if os.path.isdir(pkgpath):
            try:
                shutil.rmtree(pkgpath)
            except Exception as e:
                logger.warning('{0}: {1}'.format(type(e).__name__, e))

    return setuppath


def get_pkgdownloads(pkgjson, pkgversion):
    pkgdownloads = pkgjson['releases'][pkgversion]

    if not pkgdownloads and 'download_url' in pkgjson['info']:
        if pkgjson['info']['download_url'] and \
           pkgjson['info']['download_url'] != 'UNKNOWN':
            _url = urlparse(pkgjson['info']['download_url'])

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
                _tar = pkgjson['info']['download_url']
            pkgdownloads = [{'url': _tar, 'packagetype': 'sdist'}]
    return pkgdownloads


def get_pkgdata_from_api(pkgname):
    try:
        pkgjsonfile = urlopen(url='{0}/{1}/json'.format(pypiapiend, pkgname),
                              timeout=10).read()
    except Exception as e:
        logger.warning('JSON API error: {0}'.format(e))
    else:
        pkgj = json.loads(pkgjsonfile.decode('utf-8'))
        return dict(info=pkgj['info'], releases=pkgj['releases'])

    try:
        pypireleases = pypiserver.package_releases(pkgname)
        pkgreleases = [parse_version(v) for v in pypireleases]
        if not pkgreleases:
            raise
        pkgversion = str(sorted(pkgreleases)[-1])
        pkgurls = pypiserver.release_urls(pkgname, pkgversion)
    except Exception as e:
        logger.warning('XMLRPC API error: {0}'.format(e))
        return {}
    else:
        return {'info': {'version': pkgversion},
                'releases': {pkgversion: pkgurls}}


def get_package_list(letter_range):
    tries = 0
    while tries < 2:
        tries += 1
        try:
            logger.info('Downloading package list from PyPI ...')
            pkglist = pypiserver.list_packages()
        except Exception:
            pass
        else:
            return sorted(filter_package_list(pkglist, letter_range),
                          key=lambda s: s.lower())
    else:
        return []


def pypi(**kwargs):

    jsondict = {}
    summary_updated = 0
    summary_uptodate = 0
    summary_setup_error = 0
    summary_without_downloads = 0
    summary_no_response_from_api = 0
    summary_no_sdist = 0
    summary_no_setup = 0
    allowed_range = list(string.ascii_lowercase) + map(str, range(0, 10))
    start_time = time.time()

    logfile = kwargs.get('logfile')
    if logfile:
        logfile = os.path.abspath(logfile)
    outputfile = os.path.abspath(kwargs.get('outputfile'))
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
        raise RuntimeError(
            '"{0}" not in allowed range.'.format(
                ', '.join(set(letter_range) - set(allowed_range))))

    if not os.path.isdir(extractdir):
        os.makedirs(extractdir)

    if not os.path.isdir(cachedir):
        os.makedirs(cachedir)

    if not os.path.isfile(outputfile):
        create_file_if_notfound(outputfile)

    for pkgname in get_package_list(', '.join(letter_range)):

        if pkgname not in jsondict:
            with open(outputfile, 'r') as f:
                jsondict.update(json.loads(f.read() or '{}'))

        if pkgname not in jsondict:
            jsondict[pkgname] = {'version': '',
                                 'modules': [],
                                 'cmdline': []}

    for pkgname in sorted(jsondict.keys()):

        logger.configpkg(pkgname)

        elapsed_time = int(time.time() - start_time)
        if elapsed_time > limit_time:
            logger.configpkg()
            logger.warning('')
            logger.warning('Processing has taken more than {0} seconds.'
                           ' Interrupting.'.format(limit_time))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        mem_usage = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if mem_usage > limit_mem:
            logger.configpkg()
            logger.warning('')
            logger.warning('This process is taking more than {0} MB of memory.'
                           ' Interrupting'.format(limit_mem / (1024 * 1024)))
            logger.warning('Processing will continue in next iteration.')
            logger.warning('')
            break

        if logfile:
            logsize = int(os.path.getsize(logfile))
            if logsize > limit_log_size:
                logger.configpkg()
                logger.warning('')
                logger.warning('The log is taking more than {0} MB.'
                               ' Interrupting.'.format(logsize / (1024 * 1024)))
                logger.warning('Processing will continue in next iteration.')
                logger.warning('')
                break

        pkgjson = get_pkgdata_from_api(pkgname)

        if not pkgjson:
            logger.warning('Could not get info for this package.')
            summary_no_response_from_api += 1
            continue

        pkgversion = pkgjson['info']['version']
        oldpkgversion = jsondict[pkgname]['version']

        if oldpkgversion == pkgversion:
            logger.info('This package is up to date.')
            summary_uptodate += 1
            continue

        pkgdownloads = get_pkgdownloads(pkgjson, pkgversion)

        if not pkgdownloads:
            summary_without_downloads += 1
            logger.warning('This package does not have downloadable releases.')
            continue

        setuppath = get_setuppath(logger, pkgname, pkgversion, pkgdownloads)

        if not setuppath:
            logger.error('Could not find a suitable archive to download.')
            summary_no_sdist += 1
            continue

        if not os.path.isfile(setuppath):
            logger.error('This package has no setup script.')
            summary_no_setup += 1
            continue

        setupdir = os.path.dirname(setuppath)

        try:
            setupargs = execute_setup(wrapper, setuppath, pkgname)
            logger.info('Executing {0} ...'.format(setuppath))
        except Exception as e:
            os.chdir(setupdir)
            setupargs = {'modules': get_modules(get_packages(setupdir)),
                         'cmdline': []}
            os.chdir(basedir)
            logger.info('Inspecting {0} ...'.format(setupdir))

        try:
            shutil.rmtree(setupdir)
        except Exception as e:
            logger.warning('{0}: {1}'.format(type(e).__name__, e))

        jsondict[pkgname]['version'] = pkgversion
        jsondict[pkgname].update(setupargs)
        summary_updated += 1

    for i in sorted(set(map(lambda x: x[0].lower(), sorted(jsondict.keys())))):
        j = dict((k, v) for k, v in jsondict.iteritems() if k[0] == i)

        with open(outputfile, 'w') as f:
            f.write(u(json.dumps(j, separators=(',', ': '),
                                 sort_keys=True, indent=4)))

    summary_processed = (
        summary_updated + summary_uptodate + summary_setup_error +
        summary_no_sdist + summary_no_setup + summary_without_downloads +
        summary_no_response_from_api)
    summary_not_processed = len(jsondict.keys()) - summary_processed

    logger.configpkg('')
    logger.info('')
    logger.info('')
    logger.info('Total number of packages: {0}'.format(len(jsondict.keys())))
    logger.info('    Number of processed packages: {0}'
                .format(summary_processed))
    logger.info('        Number of updated packages: {0}'
                .format(summary_updated))
    logger.info('        Number of up-to-date packages: {0}'
                .format(summary_uptodate))
    logger.info('        Number of packages unable to read setup: {0}'
                .format(summary_setup_error))
    logger.info('        Number of packages with no source downloads: {0}'
                .format(summary_no_sdist))
    logger.info('        Number of packages without setup script: {0}'
                .format(summary_no_setup))
    logger.info('        Number of packages without downloads: {0}'
                .format(summary_without_downloads))
    logger.info('        Number of packages without response from API: {0}'
                .format(summary_no_response_from_api))
    logger.info('    Number of packages that could not be processed: {0}'
                .format(summary_not_processed))
    logger.info('')
    logger.info('')
