#!/bin/bash

set -ev

sudo chown -R ${USER}:${USER} . ${HOME}/.cache/pip

if [ -n "${PYPICONTENTSRANGE}" ]; then
	docker run -v ${PWD}:${PWD} -v ${HOME}/.cache/pip:/root/.cache/pip \
		-w ${PWD} -e PYPICONTENTSRANGE=${PYPICONTENTSRANGE} \
		luisalejandro/python:sid python main.py \
		| tee logs/${PYPICONTENTSRANGE}/pypi.log
fi

if [ -n "${STDLIBCONTENTS}" ]; then
	python stdlib.py
fi


sudo chown -R ${USER}:${USER} . ${HOME}/.cache/pip