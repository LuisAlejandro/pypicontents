# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import shutil
import tarfile
import zipfile
import threading
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
                    create_empty_json, getlogging, u, timeout)

lg = getlogging()
cachedir = os.path.join(os.environ.get('HOME'), '.cache', 'pip')
basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
wrapper = os.path.join(basedir, 'wrapper.py')
pypiapiend = 'https://pypi.python.org/pypi'
pypi = ServerProxy(pypiapiend)


def execute_setup(wrapper, setuppath, pkgname):
    errlist = []
    pybins = ['/usr/bin/python2.7', '/usr/bin/python3.5']
    pkgpath = os.path.dirname(setuppath)
    storepath = os.path.join(pkgpath, 'store.json')

    for cmd in [(pybin, wrapper, setuppath) for pybin in pybins]:
        lg.info('(%s) Parsing %s with %s' % (pkgname, setuppath, cmd[0]))

        try:
            with timeout():
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
        except Exception as e:
            p.kill()
            raise
        if os.path.isfile(storepath):
            with open(storepath) as store:
                return json.loads(store.read())
        if not stderr:
            stderr = 'Failed for unknown reason.'
        errlist.append('\n%s: %s' % (cmd[0], stderr))
    raise RuntimeError(''.join(errlist))

def get_pkgdata_from_api(pkgname):
    tries = 0
    while tries < 2:
        tries += 1
        try:
            pkgjsonfile = urlopen(url='%s/%s/json' % (pypiapiend, pkgname),
                                  timeout=10).read()
        except Exception as e:
            lg.warning('(%s) JSON API error: %s' % (pkgname, e))
        else:
            return json.loads(pkgjsonfile.decode('utf-8'))

        try:
            pkgreleases = pypi.package_releases(pkgname)
        except Exception as e:
            lg.error('(%s) XMLRPC API error: %s' % (pkgname, e))
            continue

        if not pkgreleases:
            lg.error('(%s) There are no releases for this package.' % pkgname)
            continue

        pkgversion = str(sorted([parse_version(v) for v in pkgreleases])[-1])

        try:
            return {'info': {'version': pkgversion},
                    'releases': {pkgversion: pypi.release_urls(pkgname,
                                                               pkgversion)}}
        except Exception as e:
            lg.error('(%s) XMLRPC API error: %s' % (pkgname, e))
    else:
        return False


def download_package(pkgname, arurl, arpath):
    tries = 0
    while tries < 10:
        tries += 1
        try:
            ardownobj = urlopen(url=urlesc(arurl), timeout=10).read()
        except Exception as e:
            lg.warning('(%s) Download error: %s'
                       ' (Try: %s)' % (pkgname, e, tries))
        else:
            with open(arpath, 'wb') as f:
                f.write(ardownobj)
            return True
    else:
        return False

def extract_and_list_archive(pkgname, arname, arpath, cachedir):
    arext = get_archive_extension(arpath)

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
    else:
        lg.error('(%s) Unsupported format: %s' % (pkgname, arname))
        return False

    try:
        with timeout(error='Uncompressing took too much time.'):
            with compressed(arpath, armode) as cmp:
                cmp.extractall(cachedir)
                cmplist = cmp.list()
    except Exception as e:
        lg.error('(%s) %s' % (pkgname, e))
        return False
    else:
        return cmplist

def get_package_list(lrange):
    tries = 0
    while tries < 2:
        tries += 1
        try:
            pkglist = pypi.list_packages()
        except Exception as e:
            lg.error('XMLRPC API error: %s' % e)
        else:
            return filter_package_list(pkglist, lrange)
    else:
        return []

def process(lrange='0-z'):
    jsonlist = []
    pkglist = get_package_list(lrange)

    for pkg in range(0, len(pkglist)):
        readjson = False
        writejson = False
        processsetup = False
        pkgname = pkglist[pkg]
        pkginit = pkgname[0].lower()
        pypijson = os.path.join(basedir, 'data', pkginit, 'contents.json')

        if not os.path.isfile(pypijson):
            pypijson = create_empty_json(pypijson)

        if pkg == 0:
            readjson = True
        else:
            if pkginit != pkglist[pkg-1][0].lower():
                readjson = True

        if readjson:
            with open(pypijson, 'r') as f:
                jsondict = json.loads(f.read())

        if not pkgname in jsondict:
            jsondict[pkgname] = {'version':[''],
                                 'modules':[''],
                                 'cmdline':['']}

        pkgjson = get_pkgdata_from_api(pkgname)
        if not pkgjson:
            continue

        pkgversion = pkgjson['info']['version']
        oldpkgversion = jsondict[pkgname]['version'][0]

        if oldpkgversion != pkgversion:
            pkgdownloads = pkgjson['releases'][pkgversion]
            if pkgdownloads:
                for pkgtar in pkgdownloads:
                    if pkgtar['packagetype'] == 'sdist':
                        processsetup = True
                        arurl = pkgtar['url']
                        break

        if not processsetup:
            continue

        if not os.path.isdir(cachedir):
            os.makedirs(cachedir)

        arname = os.path.basename(arurl)
        arpath = os.path.join(cachedir, arname)

        if not os.path.isfile(arpath):
            if not download_package(pkgname, arurl, arpath):
                continue

        cmplist = extract_and_list_archive(pkgname, arname, arpath,
                                           cachedir)
        if not cmplist:
            continue

        pkgdir = os.path.normpath(cmplist[0]).split(os.sep)[0]
        pkgpath = os.path.join(cachedir, pkgdir)
        setuppath = os.path.join(pkgpath, 'setup.py')

        if not os.path.isfile(setuppath):
            lg.error('(%s) No setup.py found.' % pkgname)
            continue

        os.chdir(pkgpath)
        sys.path.append(pkgpath)

        try:
            setupargs = execute_setup(wrapper, setuppath, pkgname)
        except Exception as e:
            lg.error('(%s) %s: %s' % (pkgname, type(e).__name__, e))
        else:
            jsondict[pkgname].update(setupargs)

        os.chdir(basedir)
        sys.path.remove(pkgpath)
        shutil.rmtree(pkgpath)

        if pkg == len(pkglist)-1:
            writejson = True
        else:
            if pkginit != pkglist[pkg+1][0].lower():
                writejson = True

        if writejson:
            with open(pypijson, 'w') as f:
                f.write(u(json.dumps(jsondict, separators=(',', ': '),
                                     sort_keys=True, indent=4)))
