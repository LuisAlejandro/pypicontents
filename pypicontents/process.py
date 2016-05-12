# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import shutil
import tarfile
import zipfile
import urllib2

from xmlrpclib import ServerProxy
from pkg_resources import parse_version

from .thread import execute_setup
from .utils import pygrep, get_archive_extension, urlesc

pypiapiend = 'https://pypi.python.org/pypi'
cachedir = os.path.join(os.environ['HOME'], '.cache', 'pip')
basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
pypijson = os.path.join(basedir, 'pypicontents.json')
jsondict = json.loads(open(pypijson, 'rb').read())


def process():

    pypi = ServerProxy(pypiapiend)

    for pkgname in pypi.list_packages()[0:100]:

        if not pkgname in jsondict:
            jsondict[pkgname] = {'version':[''],
                                 'modules':[''],
                                 'contents':[''],
                                 'scripts':['']}

        try:
            pkgjsonfile = urllib2.urlopen(pypiapiend+'/%s/json' % pkgname)
            pkgjson = json.loads(pkgjsonfile.read())

        except BaseException as e:
            print "[WARNING:%s] Using XMLRPC API because JSON failed: %s" % (pkgname, e)

            try:
                pkgjson = {'info': {'version': ''}, 'releases': {}}
                pkgreleases = pypi.package_releases(pkgname)

                if pkgreleases:
                    pkgreleases = [parse_version(v) for v in pkgreleases]
                    pkgversion = str(sorted(pkgreleases)[-1])
                    pkgjson['info']['version'] = pkgversion
                    pkgjson['releases'][pkgversion] = pypi.release_urls(pkgname, pkgversion)

            except BaseException as e:
                print "[ERROR:%s] XMLRPC API error: %s" % (pkgname, e)
                continue

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
                            ardownobj = urllib2.urlopen(urlesc(arurl))
                        except BaseException as e:
                            tries += 1
                            print "[WARNING:%s] Download error: %s (Try: %s)" % (pkgname,
                                                                                 e, tries)
                        else:
                            break
                    else:
                        continue

                    arfileobj = open(arpath, 'wb')
                    arfileobj.write(ardownobj.read())
                    arfileobj.close()

                arext = get_archive_extension(arpath)

                if arext == '.zip':
                    armode = 'r'
                    archive_open = zipfile.ZipFile
                    zipfile.ZipFile.list = zipfile.ZipFile.namelist

                elif (arext == '.tar.gz' or arext == '.tgz' or
                      arext == '.tar.bz2'):
                    armode = 'r:gz'
                    archive_open = tarfile.open
                    tarfile.TarFile.list = tarfile.TarFile.getnames

                    if arext == '.tar.bz2':
                        armode = 'r:bz2'

                else:
                    print '[ERROR:%s] Unsupported format: %s' % (pkgname, arname)
                    continue

                cmp = archive_open(arpath, armode)
                cmp.extractall(cachedir)
                cmplist = cmp.list()
                cmp.close()

                pkgdir = os.path.normpath(cmplist[0]).split(os.sep)[0]
                pkgpath = os.path.join(cachedir, pkgdir)
                setuppath = os.path.join(pkgpath, 'setup.py')

                if not os.path.isfile(setuppath):

                    distimp = 'from distutils.core import setup'
                    setimp = 'from setuptools import setup'

                    setuppath = (list(pygrep(distimp, pkgpath)) or
                                 list(pygrep(setimp, pkgpath)))
                    if setuppath:
                        setuppath = setuppath[0]
                    else:
                        print '[WARNING:%s] No setup.py found.' % pkgname
                        setuppath = '/dev/null'

                os.chdir(pkgpath)
                sys.path.append(pkgpath)

                try:
                    setupargs = execute_setup(setuppath)

                except BaseException as e:
                    print '[ERROR:%s] (%s) %s' % (pkgname, type(e).__name__, e)

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
                    os.remove(arpath)

                except BaseException as e:
                    print '[ERROR:%s] Post cleaning failed: %s' % (pkgname, e)

        jsonfileobj = _open(pypijson, 'wb')
        jsonfileobj.write(json.dumps(jsondict, separators=(',', ': '),
                                     sort_keys=True, indent=4))
        jsonfileobj.close()
