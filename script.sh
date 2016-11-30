#!/bin/bash

set -ev

sudo chown -R ${USER}:${USER} . ${HOME}/.cache/pip

if [ -n "${PYPICONTENTSRANGE}" ]; then
	docker run -v ${PWD}:${PWD} -v ${HOME}/.cache/pip:/root/.cache/pip \
		-w ${PWD} -e PYPICONTENTSRANGE=${PYPICONTENTSRANGE} \
		luisalejandro/pypicontents:2.7 pypirazzi process \
			-f logs/${PYPICONTENTSRANGE}/pypi.log \
			-j data/${PYPICONTENTSRANGE}/pypi.json \
			-R ${PYPICONTENTSRANGE} -L 3M -M 2G -T 2100
fi

if [ -n "${STDLIBCONTENTS}" ]; then
	docker run -v ${PWD}:${PWD} -v ${HOME}/.cache/pip:/root/.cache/pip \
		-w ${PWD} -e STDLIBCONTENTS=${STDLIBCONTENTS} \
		luisalejandro/pypicontents:${STDLIBCONTENTS} pypirazzi stdlib
fi

sudo chown -R ${USER}:${USER} . ${HOME}/.cache/pip