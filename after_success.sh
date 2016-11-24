#!/bin/bash

set -ev

if [ -n ${PYPICONTENTSRANGE} ]; then
	git checkout master
	git config --global user.name "${GITUSERNAME}"
	git config --global user.email "${GITUSERMAIL}"
	git add data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
	git commit -m "[ci skip]" data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
	git reset --hard
	git clean -fxd
	git checkout contents
	git pull origin contents
	git checkout master data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
	git add data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
	git commit -m "[ci skip] Updating PyPIContents index (letter ${PYPICONTENTSRANGE})." data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
	git push -q "https://${GHTOKEN}@${GHREPO#*//}" contents > /dev/null 2>&1
fi


if [ -n ${STDLIBCONTENTS} ]; then
	git checkout master
	git config --global user.name "${GITUSERNAME}"
	git config --global user.email "${GITUSERMAIL}"
	git add stdlib/${STDLIBCONTENTS}/stdlib.json
	git commit -m "[ci skip]" stdlib/${STDLIBCONTENTS}/stdlib.json
	git reset --hard
	git clean -fxd
	git checkout contents
	git pull origin contents
	git checkout master stdlib/${STDLIBCONTENTS}/stdlib.json
	git add stdlib/${STDLIBCONTENTS}/stdlib.json
	git commit -m "[ci skip] Updating stdlib index (version ${STDLIBCONTENTS})." stdlib/${STDLIBCONTENTS}/stdlib.json
	git push -q "https://${GHTOKEN}@${GHREPO#*//}" contents > /dev/null 2>&1
fi