.. image:: https://raw.githubusercontent.com/LuisAlejandro/pypicontents/develop/docs/_static/banner.svg

..

    PyPIContents is an application that generates a Module Index from the
    Python Package Index (PyPI) and also from various versions of the Python
    Standard Library.

.. image:: https://img.shields.io/pypi/v/pypicontents.svg
   :target: https://pypi.org/project/pypicontents/
   :alt: PyPI Package

.. image:: https://img.shields.io/github/release/LuisAlejandro/pypicontents.svg
   :target: https://github.com/LuisAlejandro/pypicontents/releases
   :alt: Github Releases

.. image:: https://img.shields.io/github/issues/LuisAlejandro/pypicontents
   :target: https://github.com/LuisAlejandro/pypicontents/issues?q=is%3Aopen
   :alt: Github Issues

.. image:: https://github.com/LuisAlejandro/pypicontents/workflows/Push/badge.svg
   :target: https://github.com/LuisAlejandro/pypicontents/actions?query=workflow%3APush
   :alt: Push

.. image:: https://coveralls.io/repos/github/LuisAlejandro/pypicontents/badge.svg?branch=develop
   :target: https://coveralls.io/github/LuisAlejandro/pypicontents?branch=develop
   :alt: Coverage

.. image:: https://cla-assistant.io/readme/badge/LuisAlejandro/pypicontents
   :target: https://cla-assistant.io/LuisAlejandro/pypicontents
   :alt: Contributor License Agreement

.. image:: https://readthedocs.org/projects/pypicontents/badge/?version=latest
   :target: https://readthedocs.org/projects/pypicontents/?badge=latest
   :alt: Read The Docs

.. image:: https://img.shields.io/discord/809504357359157288.svg?label=&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2
   :target: https://discord.gg/M36s8tTnYS
   :alt: Discord Channel

|
|

.. _different repository: https://github.com/LuisAlejandro/pypicontents-build
.. _pipsalabim: https://github.com/LuisAlejandro/pipsalabim
.. _full documentation: https://pypicontents.readthedocs.org
.. _Contents: https://www.debian.org/distrib/packages#search_contents

PyPIContents generates a configurable index written in ``JSON`` format that
serves as a database for applications like `pipsalabim`_. It can be configured
to process only a range of packages (by initial letter) and to have
memory, time or log size limits. It basically aims to mimic what the
`Contents`_ file means for a Debian based package repository, but for the
Python Package Index.

This repository stores the application. The actual index lives in a `different
repository`_ and is rebuilt weekly via Github Actions.

For more information, please read the `full documentation`_.

Getting started
===============

Installation
------------

.. _PyPI: https://pypi.org/project/pypicontents

The ``pypicontents`` program is written in python and hosted on PyPI_.
Therefore, you can use pip to install the stable version::

    $ pip install --upgrade pypicontents

If you want to install the development version (not recomended), you can
install directlty from GitHub like this::

    $ pip install --upgrade https://github.com/LuisAlejandro/pypicontents/archive/master.tar.gz

.. include:: ./USAGE.rst

Getting help
============

.. _Discord server: https://discord.gg/M36s8tTnYS
.. _StackOverflow: http://stackoverflow.com/questions/ask

If you have any doubts or problems, suscribe to our `Discord server`_ and ask for help. You can also
ask your question on StackOverflow_ (tag it ``pypicontents``) or drop me an email at luis@collagelabs.org.

Contributing
============

.. _CONTRIBUTING.rst: CONTRIBUTING.rst

See CONTRIBUTING.rst_ for details.


Release history
===============

.. _HISTORY.rst: HISTORY.rst

See HISTORY.rst_ for details.

License
=======

.. _AUTHORS.rst: AUTHORS.rst
.. _GPL-3 License: LICENSE

Copyright 2016-2022, PyPIContents Developers (read AUTHORS.rst_ for a full list of copyright holders).

Released under a `GPL-3 License`_.

Made with 💖 and 🍔
====================

.. image:: https://raw.githubusercontent.com/LuisAlejandro/pypicontents/develop/docs/_static/author-banner.svg

.. _LuisAlejandroTwitter: https://twitter.com/LuisAlejandro
.. _LuisAlejandroGitHub: https://github.com/LuisAlejandro
.. _luisalejandro.org: https://luisalejandro.org

|

    Web luisalejandro.org_ · GitHub `@LuisAlejandro`__ · Twitter `@LuisAlejandro`__

__ LuisAlejandroGitHub_
__ LuisAlejandroTwitter_
