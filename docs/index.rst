.. image:: https://rawcdn.githack.com/CollageLabs/pypicontents/02509c8c0a650cd56841dfd6f6d708af3235c485/docs/_static/title.svg

-----

.. image:: https://img.shields.io/github/release/CollageLabs/pypicontents.svg
   :target: https://github.com/CollageLabs/pypicontents/releases
   :alt: Github Releases

.. image:: https://img.shields.io/github/issues/CollageLabs/pypicontents
   :target: https://github.com/CollageLabs/pypicontents/issues?q=is%3Aopen
   :alt: Github Issues

.. image:: https://github.com/CollageLabs/pypicontents/workflows/Push/badge.svg
   :target: https://github.com/CollageLabs/pypicontents/actions?query=workflow%3APush
   :alt: Push

.. image:: https://codeclimate.com/github/CollageLabs/pypicontents/badges/gpa.svg
   :target: https://codeclimate.com/github/CollageLabs/pypicontents
   :alt: Code Climate

.. image:: https://snyk.io/test/github/CollageLabs/pypicontents/badge.svg
   :target: https://snyk.io/test/github/CollageLabs/pypicontents
   :alt: Snyk

.. image:: https://cla-assistant.io/readme/badge/CollageLabs/pypicontents
   :target: https://cla-assistant.io/CollageLabs/pypicontents
   :alt: Contributor License Agreement

.. image:: https://img.shields.io/pypi/v/pypicontents.svg
   :target: https://pypi.python.org/pypi/pypicontents
   :alt: PyPI Package

.. image:: https://readthedocs.org/projects/pypicontents/badge/?version=latest
   :target: https://readthedocs.org/projects/pypicontents/?badge=latest
   :alt: Read The Docs

.. image:: https://img.shields.io/badge/chat-discord-ff69b4.svg
   :target: https://discord.gg/M36s8tTnYS
   :alt: Discord Channel

.. _pipsalabim: https://github.com/CollageLabs/pipsalabim
.. _Contents: https://www.debian.org/distrib/packages#search_contents

PyPIContents is an application that generates a Module Index from the Python Package Index (PyPI)
and also from various versions of the Python Standard Library.

PyPIContents generates a configurable index written in ``JSON`` format that serves as a database for applications
like `pipsalabim`_. It can be configured to process only a range of packages (by initial letter) and to have
memory, time or log size limits. It basically aims to mimic what the `Contents`_ file means for a Debian
based package repository, but for the Python Package Index.

This repository stores the application in the ``master`` branch. It also stores a Module Index in the ``contents``
branch that is updated daily through a Travis cron. Read below for more information on how to use one or the other.

* Free software: GPL-3
* Documentation: https://pypicontents.readthedocs.org

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
   maintainer
