#!/bin/bash

set -ev

if [ -n ${PYPICONTENTSRANGE+x} ]; then
	docker pull luisalejandro/python:sid
	git fetch origin contents:contents
	git checkout master
	git checkout contents data/${PYPICONTENTSRANGE}/pypi.json logs/${PYPICONTENTSRANGE}/pypi.log
fi

if [ -n ${STDLIBCONTENTS+x} ]; then
	docker pull luisalejandro/python:sid
	git fetch origin contents:contents
	git checkout master
	git checkout contents stdlib/${STDLIBCONTENTS}/stdlib.json
fi
