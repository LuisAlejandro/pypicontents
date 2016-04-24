#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import shutil
import tarfile
import zipfile
import urllib2
import setuptools
import distutils

from xmlrpclib import ServerProxy
from pkg_resources import parse_version

from helper import (fake_distribute_setup, dummysetup,
                    dummyexit, pygrep)


os._exit = dummyexit
sys.exit = dummyexit
setuptools.setup = dummysetup
distutils.core.setup = dummysetup
sys.modules['distribute_setup'] = fake_distribute_setup

distimp = 'from distutils.core import setup'
setimp = 'from setuptools import setup'

scriptdir = os.path.dirname(os.path.realpath(__file__))
pypijson = os.path.join(scriptdir, 'pypi-contents.json')
cachedir = os.path.join(os.environ['HOME'], '.cache', 'pip')

with open(pypijson, 'rb') as jsonfile:
    jsondict = json.loads(jsonfile.read())

pypi = ServerProxy('https://pypi.python.org/pypi')

for pkgname in pypi.list_packages():

    if not pkgname in jsondict:
        jsondict[pkgname] = {'version':[''],
                             'modules':[''],
                             'scripts':[''],
                             'contents':['']}

    pkgreleases = pypi.package_releases(pkgname)

    if pkgreleases:
        pkgreleases = [parse_version(v) for v in pkgreleases]
        pkgversion = str(sorted(pkgreleases)[-1])
        oldver = jsondict[pkgname]['version'][0]

        if oldver != pkgversion:

            arurl = ''
            for pkgtar in pypi.release_urls(pkgname, pkgversion):
                if pkgtar['python_version'] == 'source':
                    arurl = pkgtar['url']
                    break

            if arurl:
                print 'Updating package "%s" (%s > %s) ...' % (pkgname, oldver,
                                                               pkgversion)
                arname = os.path.basename(arurl)
                arpath = os.path.join(cachedir, arname)

                if not os.path.isfile(arpath):
                    ardownobj = urllib2.urlopen(arurl)

                    with open(arpath, 'wb') as arfileobj:
                        arfileobj.write(ardownobj.read())

                if arpath.endswith('.zip'):
                    armode = 'r'
                    archive_open = zipfile.ZipFile
                    zipfile.ZipFile.list = zipfile.ZipFile.namelist

                elif arpath.endswith('.tar.gz'):
                    armode = 'r:gz'
                    archive_open = tarfile.open
                    tarfile.TarFile.list = tarfile.TarFile.getnames

                elif arpath.endswith('.tar.bz2'):
                    armode = 'r:bz2'
                    archive_open = tarfile.open
                    tarfile.TarFile.list = tarfile.TarFile.getnames

                else:
                    print 'NO SE QUE ES: '+arurl

                cmp = archive_open(arpath, armode)
                cmp.extractall(cachedir)
                cmplist = cmp.list()
                cmp.close()

                pkgdir = os.path.normpath(cmplist[0]).split(os.sep)[0]
                pkgpath = os.path.join(cachedir, pkgdir)
                setuppath = os.path.join(pkgpath, 'setup.py')

                if not os.path.isfile(setuppath):
                    setuppath = (list(pygrep(distimp, pkgpath)) or
                                 list(pygrep(setimp, pkgpath)))
                    if setuppath:
                        setuppath = setuppath[0]

                with open(setuppath, 'rb') as setuppy:
                    setuppyconts = setuppy.read()

                os.chdir(pkgpath)
                sys.path.append(pkgpath)

                try:
                    setupargs = {}
                    exec setuppyconts
                except Exception as e:
                    print '[FAILED] setup.py failed with %s' % e
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

                os.chdir(scriptdir)
                sys.path.remove(pkgpath)
                shutil.rmtree(pkgpath)
                # os.remove(arpath)

with open(pypijson, 'wb') as jsonfileobj:
    jsonfileobj.write(json.dumps(jsondict, indent=4,
                                 sort_keys=True, separators=(',', ': ')))

