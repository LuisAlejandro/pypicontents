# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import json
import glob
import shutil
import tarfile
import zipfile

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

from pkg_resources import parse_version

from .thread import execute_setup
from .utils import (get_archive_extension, urlesc, filter_package_list,
                    create_empty_json, getlogging, u, timeout)


def process(lrange='0-z'):
    if not lrange:
        lrange = '0-z'

    lg = getlogging()
    pypiapiend = 'https://pypi.python.org/pypi'
    cachedir = os.path.join(os.environ['HOME'], '.cache', 'pip')
    basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    pypi = ServerProxy(pypiapiend)

    for pkgname in filter_package_list(pypi.list_packages(), lrange):
        pypijson = os.path.join(basedir, 'data', pkgname[0].lower(), 'contents.json')

        if not os.path.isfile(pypijson):
            pypijson = create_empty_json(pypijson)

        with open(pypijson, 'r') as f:
            jsondict = json.loads(f.read())

        if not pkgname in jsondict:
            jsondict[pkgname] = {'version':[''],
                                 'modules':[''],
                                 'contents':[''],
                                 'scripts':['']}
        try:
            pkgjsonfile = urlopen(url='%s/%s/json' % (pypiapiend, pkgname),
                                  timeout=10).read()
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            try:
                lg.warning('(%s) JSON API error: %s' % (pkgname, e))
                pkgjson = {'info': {'version': ''}, 'releases': {}}
                pkgreleases = pypi.package_releases(pkgname)
                if pkgreleases:
                    pkgreleases = [parse_version(v) for v in pkgreleases]
                    pkgversion = str(sorted(pkgreleases)[-1])
                    pkgjson['info']['version'] = pkgversion
                    pkgjson['releases'][pkgversion] = pypi.release_urls(pkgname,pkgversion)
                else:
                    raise RuntimeError('There are no releases for this package.')
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                lg.error('(%s) XMLRPC API error: %s' % (pkgname, e))
                continue
        else:
            pkgjson = json.loads(pkgjsonfile.decode('utf-8'))

        pkgversion = pkgjson['info']['version']
        oldpkgversion = jsondict[pkgname]['version'][0]

        if oldpkgversion != pkgversion:
            pkgdownloads = pkgjson['releases'][pkgversion]

            if pkgdownloads:
                for pkgtar in pkgdownloads:
                    if pkgtar['packagetype'] == 'sdist':
                        arurl = pkgtar['url']
                        break

                arname = os.path.basename(arurl)
                arpath = os.path.join(cachedir, arname)

                if not os.path.isfile(arpath):
                    tries = 0
                    while tries < 10:
                        try:
                            ardownobj = urlopen(url=urlesc(arurl), timeout=10).read()
                        except KeyboardInterrupt:
                            raise
                        except BaseException as e:
                            tries += 1
                            lg.warning('(%s) Download error: %s'
                                       ' (Try: %s)' % (pkgname, e, tries))
                        else:
                            break
                    else:
                        continue

                    with open(arpath, 'wb') as f:
                        f.write(ardownobj)

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
                    continue

                try:
                    with timeout(error='Uncompressing took too much time.'):
                        with compressed(arpath, armode) as cmp:
                            cmp.extractall(cachedir)
                            cmplist = cmp.list()
                except KeyboardInterrupt:
                    raise
                except BaseException as e:
                    lg.error('(%s) %s' % (pkgname, e))
                    continue

                pkgdir = os.path.normpath(cmplist[0]).split(os.sep)[0]
                pkgpath = os.path.join(cachedir, pkgdir)
                setuppath = os.path.join(pkgpath, 'setup.py')

                lg.info('(%s) Processing %s' % (pkgname, setuppath))

                if not os.path.isfile(setuppath):
                    lg.error('(%s) No setup.py found.' % pkgname)
                    continue

                os.chdir(pkgpath)
                sys.path.append(pkgpath)

                try:
                    setupargs = execute_setup(setuppath)
                except KeyboardInterrupt:
                    raise
                except BaseException as e:
                    lg.error('(%s) %s: %s' % (pkgname, type(e).__name__, e))
                else:
                    if 'py_modules' in setupargs:
                        jsondict[pkgname]['modules'] = setupargs['py_modules']

                    if 'packages' in setupargs:
                        if setupargs['packages']:
                            if setupargs['packages'][0]:
                                jsondict[pkgname]['modules'] = setupargs['packages']
                            else:
                                pys = glob.glob(os.path.join(pkgpath, '*.py'))
                                pys = [os.path.splitext(os.path.basename(p))[0] for p in pys if
                                       os.path.basename(p) != 'setup.py']
                                jsondict[pkgname]['modules'] = pys

                    if 'scripts' in setupargs:
                        jsondict[pkgname]['scripts'] = setupargs['scripts']

                    jsondict[pkgname]['contents'] = cmplist
                    jsondict[pkgname]['version'][0] = pkgversion

                try:
                    os.chdir(basedir)
                    sys.path.remove(pkgpath)
                    shutil.rmtree(pkgpath)
                except KeyboardInterrupt:
                    raise
                except BaseException as e:
                    lg.error('(%s) Post cleaning failed: %s' % (pkgname, e))

        with open(pypijson, 'w') as f:
            f.write(u(json.dumps(jsondict, separators=(',', ': '),
                                 sort_keys=True, indent=4)))
