# -*- coding: utf-8 -*-

import os
import time
import json
import shutil
import tarfile
import zipfile
import pkgutil
from subprocess import Popen, PIPE
from distutils import sysconfig

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
from setuptools import find_packages

from .utils import (get_archive_extension, urlesc, filter_package_list,
                    create_file_if_notfound, logger, u, timeout,
                    find_files, list_files, is_valid_path,
                    custom_sys_path, remove_sys_modules)

libdir = sysconfig.get_config_var('LIBDEST')
extractdir = os.path.join('/tmp', 'pypicontents')
cachedir = os.path.join(os.environ.get('HOME'), '.cache', 'pip')
basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
wrapper = os.path.join(basedir, 'wrapper.py')
pypiapiend = 'https://pypi.python.org/pypi'
pypi = ServerProxy(pypiapiend)


def get_package_dirs(path):
    """
    List directories containing python packages on ``path``.

    :param path: a path pointing to a directory containing python code.
    :return: a list containing directories of packages.

    .. versionadded:: 0.1.0
    """
    package_dirs = []
    for init in find_files(path, '__init__.py'):
        pkgdir = os.path.dirname(init)
        if os.path.commonprefix([pkgdir, path]) == path and \
           is_valid_path(os.path.relpath(pkgdir, path)):
            while True:
                init = os.path.split(init)[0]
                if not os.path.isfile(os.path.join(init, '__init__.py')):
                    break
            if init not in package_dirs:
                package_dirs.append(init)
    return package_dirs


def get_packages(path):
    """
    List packages living in ``path`` with its directory.

    :param path: a path pointing to a directory containing python code.
    :return: a list of tuples containing the name of the package and
             the package directory. For example::

                 [
                    ('package_a', '/path/to/package_a'),
                    ('package_b.module_b', '/path/to/package_b/module_b'),
                    ('package_c.module_c', '/path/to/package_c/module_c')
                 ]

    .. versionadded:: 0.1.0
    """
    packages = []
    package_dirs = get_package_dirs(path)

    for _dir in package_dirs:
        for pkgname in find_packages(_dir):
            try:
                with custom_sys_path([_dir, libdir]):
                    with remove_sys_modules([pkgname]):
                        pkgdir = pkgutil.get_loader(pkgname).filename
            except:
                pkgdir = os.path.join(_dir, os.sep.join(pkgname.split('.')))
            packages.append([pkgname, pkgdir])
    return packages


def get_modules(pkgdata):
    """
    List modules inside packages provided in ``pkgdata``.

    :param pkgdata: a list of tuples containing the name of a package and
                    the directory where its located.
    :return: a list of the modules according to the list of packages
             provided in ``pkgdata``.

    .. versionadded:: 0.1.0
    """
    modules = []

    for pkgname, pkgdir in pkgdata:
        for py in list_files(pkgdir, '*.py'):
            module = os.path.splitext(os.path.basename(py))[0]
            if not module.startswith('__'):
                modname = '.'.join([pkgname, module])
            else:
                modname = pkgname
            modules.append(modname)
    return sorted(list(set(modules)))


def execute_setup(wrapper, setuppath, pkgname):
    errlist = []
    pybins = ['/usr/bin/python2.7', '/usr/bin/python3.5']
    pkgpath = os.path.dirname(setuppath)
    storepath = os.path.join(pkgpath, 'store.json')

    for cmd in [(pybin, wrapper, setuppath) for pybin in pybins]:
        try:
            with timeout(error='Execution of setup.py took too much time.'):
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
        except Exception:
            p.kill()
            raise
        if os.path.isfile(storepath):
            with open(storepath) as store:
                return json.loads(store.read())
        if not stderr:
            stderr = 'Failed for unknown reason.'
        errlist.append('(%s) %s' % (cmd[0], stderr))
    raise RuntimeError(' '.join(errlist))


def get_pkgdata_from_api(logger, pkgname):
    try:
        pkgjsonfile = urlopen(url='%s/%s/json' % (pypiapiend, pkgname),
                              timeout=10).read()
    except Exception as e:
        logger.warning('(%s) JSON API error: %s' % (pkgname, e))
    else:
        pkgj = json.loads(pkgjsonfile.decode('utf-8'))
        return dict(info=pkgj['info'], releases=pkgj['releases'])

    try:
        pkgreleases = [parse_version(v) for v in pypi.package_releases(pkgname)]
        if not pkgreleases:
            raise
        pkgversion = str(sorted(pkgreleases)[-1])
        pkgurls = pypi.release_urls(pkgname, pkgversion)
    except Exception as e:
        logger.warning('(%s) XMLRPC API error: %s' % (pkgname, e))
        return {}
    else:
        return {'info': {'version': pkgversion},
                'releases': {pkgversion: pkgurls}}


def download_archive(logger, pkgname, arurl, arpath):
    tries = 0
    while tries < 5:
        tries += 1
        try:
            ardownobj = urlopen(url=urlesc(arurl), timeout=10).read()
        except Exception as e:
            logger.warning('(%s) Download error: %s (Try: %s)' % (pkgname, e, tries))
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
        logger.error('(%s) %s: %s' % (pkgname, type(e).__name__, e))
        return False
    else:
        return arlist


def get_package_list(lrange):
    tries = 0
    while tries < 2:
        tries += 1
        try:
            pkglist = pypi.list_packages()
        except Exception:
            pass
        else:
            return sorted(filter_package_list(pkglist, lrange),
                          key=lambda s: s.lower())
    else:
        return []


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
                logger.warning('(%s) There was an error downloading this package.' % pkgname)
                continue

        arlist = get_archive_filelist(logger, pkgname, arname, arpath, arext,
                                      extractdir)
        if not arlist:
            logger.warning('(%s) There was an error extracting this package.' % pkgname)
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))
            continue

        pkgtopdir = arlist[0].split(os.sep)[0]

        if pkgtopdir == '.':
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))
            continue

        pkgpath = os.path.normpath(os.path.join(extractdir, pkgtopdir))
        setuppath = os.path.join(pkgpath, 'setup.py')

        if os.path.isfile(setuppath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))
            break

        pkgpath = extractdir
        setuppath = os.path.join(pkgpath, 'setup.py')

        if os.path.isfile(setuppath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))
            break

        if os.path.isfile(arpath):
            try:
                os.remove(arpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))

        if os.path.isdir(pkgpath):
            try:
                shutil.rmtree(pkgpath)
            except Exception as e:
                logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))

    return setuppath


def process(lrange='0-z'):

    if not os.path.isdir(extractdir):
        os.makedirs(extractdir)

    if not os.path.isdir(cachedir):
        os.makedirs(cachedir)

    jsondict = {}
    pkglist = get_package_list(lrange)

    summary_updated = 0
    summary_uptodate = 0
    summary_setup_error = 0
    summary_without_downloads = 0
    summary_no_response_from_api = 0
    summary_no_sdist = 0
    summary_no_setup = 0
    start_time = time.time()

    for pkgname in pkglist:

        pypijson = os.path.join(basedir, 'data', pkgname[0].lower(), 'pypi.json')

        if not os.path.isfile(pypijson):
            create_file_if_notfound(pypijson)

        if pkgname not in jsondict:
            with open(pypijson, 'r') as f:
                jsondict.update(json.loads(f.read() or '{}'))

        if pkgname not in jsondict:
            jsondict[pkgname] = {'version': '',
                                 'modules': [],
                                 'cmdline': []}

    for pkgname in sorted(jsondict.keys()):

        pypilog = os.path.join(basedir, 'logs', pkgname[0].lower(), 'pypi.log')

        if not os.path.isfile(pypilog):
            create_file_if_notfound(pypilog)

        logger.config(pypilog)

        if time.time() - start_time >= 2100:
            print
            logger.warning('Processing has taken more than 35min. Interrupting.')
            logger.warning('Processing will continue in next iteration.')
            break

        pkgjson = get_pkgdata_from_api(logger, pkgname)

        if not pkgjson:
            logger.warning('(%s) Could not get info for this package.' % pkgname)
            summary_no_response_from_api += 1
            continue

        pkgversion = pkgjson['info']['version']
        oldpkgversion = jsondict[pkgname]['version']

        if oldpkgversion == pkgversion:
            logger.info('(%s) This package is up to date.' % pkgname)
            summary_uptodate += 1
            continue

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

        if not pkgdownloads:
            summary_without_downloads += 1
            logger.warning('(%s) This package does not have downloadable releases.' % pkgname)
            continue

        setuppath = get_setuppath(logger, pkgname, pkgversion, pkgdownloads)

        if not setuppath:
            logger.error('(%s) Could not find a suitable archive to download.' % pkgname)
            summary_no_sdist += 1
            continue

        if not os.path.isfile(setuppath):
            logger.error('(%s) This package has no setup script.' % pkgname)
            summary_no_setup += 1
            continue

        setupdir = os.path.dirname(setuppath)

        try:
            setupargs = execute_setup(wrapper, setuppath, pkgname)
            logger.info('(%s) Executing %s ...' % (pkgname, setuppath))
        except Exception as e:
            os.chdir(setupdir)
            setupargs = {'modules': get_modules(get_packages(setupdir)),
                         'cmdline': []}
            os.chdir(basedir)
            logger.info('(%s) Inspecting %s ...' % (pkgname, setupdir))

        try:
            shutil.rmtree(setupdir)
        except Exception as e:
            logger.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))

        jsondict[pkgname]['version'] = pkgversion
        jsondict[pkgname].update(setupargs)
        summary_updated += 1

    for i in sorted(set(map(lambda x: x[0].lower(), sorted(jsondict.keys())))):
        pypijson = os.path.join(basedir, 'data', i, 'pypi.json')
        j = dict((k, v) for k, v in jsondict.iteritems() if k[0] == i)

        with open(pypijson, 'w') as f:
            f.write(u(json.dumps(j, separators=(',', ': '),
                                 sort_keys=True, indent=4)))

    summary_processed = (
        summary_updated + summary_uptodate + summary_setup_error +
        summary_no_sdist + summary_no_setup + summary_without_downloads +
        summary_no_response_from_api)
    summary_not_processed = len(jsondict.keys()) - summary_processed

    print
    print
    print 'Total number of packages: %s' % len(jsondict.keys())
    print '    Number of processed packages: %s' % summary_processed
    print '        Number of updated packages: %s' % summary_updated
    print '        Number of up-to-date packages: %s' % summary_uptodate
    print '        Number of packages unable to read setup: %s' % summary_setup_error
    print '        Number of packages with no source downloads: %s' % summary_no_sdist
    print '        Number of packages without setup script: %s' % summary_no_setup
    print '        Number of packages without downloads: %s' % summary_without_downloads
    print '        Number of packages without response from API: %s' % summary_no_response_from_api
    print '    Number of packages that could not be processed: %s' % summary_not_processed
    print
    print
