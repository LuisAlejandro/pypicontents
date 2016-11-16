# -*- coding: utf-8 -*-

import os
import time
import json
import shutil
import tarfile
import zipfile
from subprocess import Popen, PIPE

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

from pkg_resources import parse_version

from .utils import (get_archive_extension, urlesc, filter_package_list,
                    create_file_if_notfound, getlogging, u, timeout)

extractdir = os.path.join('/tmp', 'pypicontents')
cachedir = os.path.join(os.environ.get('HOME'), '.cache', 'pip')
basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
wrapper = os.path.join(basedir, 'wrapper.py')
pypiapiend = 'https://pypi.python.org/pypi'
pypi = ServerProxy(pypiapiend)


def execute_setup(lg, wrapper, setuppath, pkgname):
    errlist = []
    pybins = ['/usr/bin/python2.7', '/usr/bin/python3.5']
    pkgpath = os.path.dirname(setuppath)
    storepath = os.path.join(pkgpath, 'store.json')

    for cmd in [(pybin, wrapper, setuppath) for pybin in pybins]:
        lg.info('(%s) Parsing %s with %s' % (pkgname, setuppath, cmd[0]))

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


def get_pkgdata_from_api(lg, pkgname):
    try:
        pkgjsonfile = urlopen(url='%s/%s/json' % (pypiapiend, pkgname),
                              timeout=10).read()
    except Exception as e:
        lg.warning('(%s) JSON API error: %s' % (pkgname, e))
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
        lg.warning('(%s) XMLRPC API error: %s' % (pkgname, e))
        return {}
    else:
        return {'info': {'version': pkgversion},
                'releases': {pkgversion: pkgurls}}


def download_archive(lg, pkgname, arurl, arpath):
    tries = 0
    while tries < 10:
        tries += 1
        try:
            ardownobj = urlopen(url=urlesc(arurl), timeout=10).read()
        except Exception as e:
            lg.warning('(%s) Download error: %s (Try: %s)' % (pkgname, e, tries))
        else:
            with open(arpath, 'wb') as f:
                f.write(ardownobj)
            return True
    else:
        return False


def get_archive_filelist(lg, pkgname, arname, arpath, arext, extractdir):
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
            with compressed(arpath, armode) as cmp:
                cmp.extractall(extractdir)
                arlist = cmp.list()
    except Exception as e:
        lg.error('(%s) %s: %s' % (pkgname, type(e).__name__, e))
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


def process(lrange='0-z'):

    if not os.path.isdir(extractdir):
        os.makedirs(extractdir)

    if not os.path.isdir(cachedir):
        os.makedirs(cachedir)

    jsondict = {}
    pkglist = get_package_list(lrange)

    summary_updated = 0
    summary_uptodate = 0
    summary_error = 0
    summary_without_downloads = 0
    summary_no_response_from_api = 0

    start_time = time.time()

    for pkgname in pkglist:

        pypijson = os.path.join(basedir, 'data', pkgname[0].lower(), 'contents.json')

        if not os.path.isfile(pypijson):
            create_file_if_notfound(pypijson)

        if pkgname not in jsondict:
            with open(pypijson, 'r') as f:
                jsondict.update(json.loads(f.read() or '{}'))

        if pkgname not in jsondict:
            jsondict[pkgname] = {'version': '',
                                 'modules': [],
                                 'cmdline': []}

    for pkgname in pkglist:

        if time.time() - start_time >= 2100:
            print
            lg.warning('Processing has taken more than 35min. Interrupting.')
            lg.warning('Processing will continue in next iteration.')
            break

        pypilog = os.path.join(basedir, 'logs', pkgname[0].lower(), 'contents.log')

        if not os.path.isfile(pypilog):
            create_file_if_notfound(pypilog)

        lg = getlogging(pypilog)

        pkgjson = get_pkgdata_from_api(lg, pkgname)

        if not pkgjson:
            lg.warning('(%s) Could not get info for this package.' % pkgname)
            summary_no_response_from_api += 1
            continue

        pkgversion = pkgjson['info']['version']
        oldpkgversion = jsondict[pkgname]['version']

        if oldpkgversion == pkgversion:
            summary_uptodate += 1
            lg.info('(%s) This package is up to date.' % pkgname)
            continue

        pkgdownloads = pkgjson['releases'][pkgversion]

        if not pkgdownloads:
            summary_without_downloads += 1
            lg.warning('(%s) This package does not have downloadable releases.' % pkgname)
            continue

        for pkgtar in pkgdownloads:
            pkgpath = None
            setuppath = None
            arlist = None
            arpath = None
            arname = None
            arurl = None
            arext = None
            pkgtopdir = None

            if pkgtar['packagetype'] not in ['sdist', 'bdist_egg']:
                continue

            arurl = pkgtar['url']
            arname = os.path.basename(arurl)
            arpath = os.path.join(cachedir, arname)
            arext = get_archive_extension(arpath)

            if arext not in ['.zip', '.tgz', '.tar.gz', '.tar.bz2']:
                continue

            if not os.path.isfile(arpath):
                if not download_archive(lg, pkgname, arurl, arpath):
                    lg.warning('(%s) There was an error downloading this package.' % pkgname)
                    continue

            arlist = get_archive_filelist(lg, pkgname, arname, arpath, arext,
                                          extractdir)
            if not arlist:
                lg.warning('(%s) There was an error extracting this package.' % pkgname)
                continue

            pkgtopdir = arlist[0].split(os.sep)[0]

            if pkgtopdir == '.':
                continue

            pkgpath = os.path.normpath(os.path.join(extractdir, pkgtopdir))
            setuppath = os.path.join(pkgpath, 'setup.py')

            if os.path.isfile(setuppath):
                break

            pkgpath = extractdir
            setuppath = os.path.join(pkgpath, 'setup.py')

            if os.path.isfile(setuppath):
                break

            try:
                os.remove(arpath)
                shutil.rmtree(pkgpath)
            except Exception as e:
                lg.warning('(%s) %s: %s' % (pkgname, type(e).__name__, e))

        if not setuppath:
            lg.error('(%s) Could not find a suitable archive to download.' % pkgname)
            summary_error += 1
            continue

        if not os.path.isfile(setuppath):
            lg.error('(%s) This package has no setup script.' % pkgname)
            summary_error += 1
            continue

        try:
            setupargs = execute_setup(lg, wrapper, setuppath, pkgname)
        except Exception as e:
            lg.error('(%s) %s: %s' % (pkgname, type(e).__name__, e))
            summary_error += 1
            continue
        else:
            jsondict[pkgname]['version'] = pkgversion
            jsondict[pkgname].update(setupargs)
            summary_updated += 1

    for i in sorted(set(map(lambda x: x[0].lower(), pkglist))):
        pypijson = os.path.join(basedir, 'data', i, 'contents.json')
        j = dict((k, v) for k, v in jsondict.iteritems() if k[0] == i)

        with open(pypijson, 'w') as f:
            f.write(u(json.dumps(j, separators=(',', ': '),
                                 sort_keys=True, indent=4)))

    summary_processed = (summary_updated + summary_uptodate + summary_error +
                         summary_without_downloads +
                         summary_no_response_from_api)
    summary_not_processed = len(pkglist) - summary_processed

    print
    print
    print 'Total number of packages: %s' % len(pkglist)
    print '    Number of processed packages: %s' % summary_processed
    print '        Number of updated packages: %s' % summary_updated
    print '        Number of up-to-date packages: %s' % summary_uptodate
    print '        Number of errored packages: %s' % summary_error
    print '        Number of packages without downloads: %s' % summary_without_downloads
    print '        Number of packages without response from API: %s' % summary_no_response_from_api
    print '    Number of packages that could not be processed: %s' % summary_not_processed
    print
    print
