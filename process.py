#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
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


def pygrep(pattern, dir):
    r = re.compile(pattern)
    for parent, dnames, fnames in os.walk(dir):
        for fname in fnames:
            filename = os.path.join(parent, fname)
            if os.path.isfile(filename):
                with open(filename) as f:
                    for line in f:
                        if r.search(line):
                            yield filename

def dummysetup(*args, **kwargs):
    global setupargs
    setupargs = kwargs

setuptools.setup = dummysetup
distutils.core.setup = dummysetup

distimp = 'from distutils.core import setup'
setimp = 'from setuptools import setup'

scriptdir = os.path.dirname(os.path.realpath(__file__))
pypijson = os.path.join(scriptdir, 'pypi-contents.json')
cachedir = os.path.join(os.environ['HOME'], '.cache', 'pip')

with open(pypijson, 'r') as jsonfile:
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

                ardownobj = urllib2.urlopen(arurl)

                with open(arpath, 'w') as arfileobj:
                    arfileobj.write(ardownobj.read())

                if arurl.endswith('.zip'):
                    armode = 'r'
                    archive_open = zipfile.ZipFile
                    zipfile.ZipFile.list = zipfile.ZipFile.namelist

                elif arurl.endswith('.tar.gz'):
                    armode = 'r:gz'
                    archive_open = tarfile.open
                    tarfile.TarFile.list = tarfile.TarFile.getnames

                elif arurl.endswith('.tar.bz2'):
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

                with open(setuppath, 'r') as setuppy:
                    setuppyconts = setuppy.read()

                os.chdir(pkgpath)
                sys.path.append(pkgpath)

                try:
                    setupargs = {}
                    exec setuppyconts
                except Exception as e:
                    print '[FAILED] setup.py failed with: %s' % e

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
                os.remove(arpath)

with open(pypijson, 'w') as jsonfileobj:
    jsonfileobj.write(json.dumps(jsondict, indent=4,
                                 sort_keys=True, separators=(',', ': ')))

