.. image:: https://gitcdn.xyz/repo/LuisAlejandro/pypicontents/master/docs/_static/title.svg

-----

.. image:: https://img.shields.io/pypi/v/pypicontents.svg
   :target: https://pypi.python.org/pypi/pypicontents
   :alt: PyPI Package

.. image:: https://img.shields.io/travis/LuisAlejandro/pypicontents.svg
   :target: https://travis-ci.org/LuisAlejandro/pypicontents
   :alt: Travis CI

.. image:: https://coveralls.io/repos/github/LuisAlejandro/pypicontents/badge.svg?branch=master
   :target: https://coveralls.io/github/LuisAlejandro/pypicontents?branch=master
   :alt: Coveralls

.. image:: https://landscape.io/github/LuisAlejandro/pypicontents/master/landscape.svg?style=flat
   :target: https://landscape.io/github/LuisAlejandro/pypicontents/master
   :alt: Landscape

.. image:: https://readthedocs.org/projects/pypicontents/badge/?version=latest
   :target: https://readthedocs.org/projects/pypicontents/?badge=latest
   :alt: Read The Docs

.. image:: https://cla-assistant.io/LuisAlejandro/pypicontents
   :target: https://cla-assistant.io/readme/badge/LuisAlejandro/pypicontents
   :alt: Contributor License Agreement

.. image:: https://badges.gitter.im/LuisAlejandro/pypicontents.svg
   :target: https://gitter.im/LuisAlejandro/pypicontents
   :alt: Gitter Chat

PyPIContents is an assistant to guess your pip dependencies from your code, without using a
requirements file.

PyPIContents will tell you which packages you need to install to satisfy the dependencies of
your project. It uses a simple AST visitor for detecting imports and `PyPIContents`_ to
search which packages contain these imports.

* Free software: GPL-3
* Documentation: https://pypicontents.readthedocs.org

.. _PyPIContents: https://github.com/LuisAlejandro/pypicontents

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   installation
   usage
   api
   contributing
   authors
   history
