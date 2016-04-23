import os
import json
import glob
import tarfile
import zipfile
import urllib2
from xmlrpclib import ServerProxy

jsondict ={}
cachedir = '/tmp/tempkgs/'

pypi = ServerProxy('https://pypi.python.org/pypi')

for pkgname in pypi.list_packages():
    pkgreleases = sorted(pypi.package_releases(pkgname))

    if pkgreleases:
        pkgversion = pkgreleases[0]

        for pkgtar in pypi.release_urls(pkgname, pkgversion):
            if pkgtar['python_version'] == 'source':
                arurl = pkgtar['url']
                arname = os.path.basename(arurl)
                arpath = cachedir+arname

                if not os.path.isfile(arpath):
                    for oldar in glob.glob(cachedir+pkgname+'-*'):
                        os.remove(oldar)

                    ardownobj = urllib2.urlopen(arurl)
                    arfileobj = open(arpath, 'w')
                    arfileobj.write(ardownobj.read())
                    arfileobj.close()

                if arurl.endswith('.zip'):
                    archive_open = zipfile.ZipFile
                    zipfile.ZipFile.list = zipfile.ZipFile.namelist
                    zipfile.ZipFile.openfile = zipfile.ZipFile.open

                elif arurl.endswith('.tar.gz'):
                    archive_open = tarfile.open
                    tarfile.TarFile.list = tarfile.TarFile.getnames
                    tarfile.TarFile.openfile = tarfile.TarFile.extractfile

                cmp = archive_open(arpath, 'r')
                cmplist = cmp.list()
                jsondict[pkgname] = {'contents': cmplist}

                for f in cmplist:
                    fdirname = os.path.dirname(f)
                    fbasename = os.path.basename(f)

                    if (fdirname.endswith('.egg-info') and
                        fbasename == 'top_level.txt'):
                        modulesobj = cmp.openfile(f)
                        pkgmodules = modulesobj.read()
                        jsondict[pkgname].update(
                            {'modules': filter(None, pkgmodules.split('\n'))})
                        modulesobj.close()
                cmp.close()

jsonfileobj = open('pypi-contents.json', 'w')
jsonfileobj.write(json.dumps(jsondict))
jsonfileobj.close()

