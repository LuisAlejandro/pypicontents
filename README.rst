.. image:: https://gitcdn.xyz/repo/LuisAlejandro/pypicontents/master/docs/_static/banner.svg

..

    PyPIContents is an application that generates a Module Index from the Python Package Index (PyPI)
    and also from various versions of the Python Standard Library.

.. image:: https://img.shields.io/pypi/v/pypicontents.svg
   :target: https://pypi.python.org/pypi/pypicontents
   :alt: PyPI Package

.. image:: https://img.shields.io/travis/LuisAlejandro/pypicontents.svg
   :target: https://travis-ci.org/LuisAlejandro/pypicontents
   :alt: Travis CI

.. image:: https://coveralls.io/repos/github/LuisAlejandro/pypicontents/badge.svg?branch=master
   :target: https://coveralls.io/github/LuisAlejandro/pypicontents?branch=master
   :alt: Coveralls

.. image:: https://codeclimate.com/github/LuisAlejandro/pypicontents/badges/gpa.svg
   :target: https://codeclimate.com/github/LuisAlejandro/pypicontents
   :alt: Code Climate

.. image:: https://pyup.io/repos/github/LuisAlejandro/pipsalabim/shield.svg
   :target: https://pyup.io/repos/github/LuisAlejandro/pipsalabim/
   :alt: Updates

.. image:: https://readthedocs.org/projects/pypicontents/badge/?version=latest
   :target: https://readthedocs.org/projects/pypicontents/?badge=latest
   :alt: Read The Docs

.. image:: https://cla-assistant.io/readme/badge/LuisAlejandro/pypicontents
   :target: https://cla-assistant.io/LuisAlejandro/pypicontents
   :alt: Contributor License Agreement

.. image:: https://badges.gitter.im/LuisAlejandro/pypicontents.svg
   :target: https://gitter.im/LuisAlejandro/pypicontents
   :alt: Gitter Chat

|
|

.. _pipsalabim: https://github.com/LuisAlejandro/pipsalabim
.. _full documentation: https://pypicontents.readthedocs.org
.. _Contents: https://www.debian.org/distrib/packages#search_contents

PyPIContents generates a configurable index written in ``JSON`` format that serves as a database for applications
like `pipsalabim`_. It can be configured to process only a range of packages (by initial letter) and to have
memory, time or log size limits. It basically aims to mimic what the `Contents`_ file means for a Debian
based package repository, but for the Python Package Index.

This repository stores the application in the ``master`` branch. It also stores a Module Index in the ``contents``
branch that is updated daily through a Travis cron. Read below for more information on how to use one or the other.

For more information, please read the `full documentation`_.

Getting started
===============

Installation
------------

.. _PyPI: https://pypi.python.org/pypi/pypicontents

The ``pypicontents`` program is written in python and hosted on PyPI_. Therefore, you can use
pip to install the stable version::

    $ pip install --upgrade pypicontents

If you want to install the development version (not recomended), you can install
directlty from GitHub like this::

    $ pip install --upgrade https://github.com/LuisAlejandro/pypicontents/archive/master.tar.gz

Using the application
---------------------

PyPIContents is divided in several commands.

pypicontents pypi
~~~~~~~~~~~~~~~~~

This command generates a JSON module index with information from PyPI. Read below for more information
on how to use it::

    $ pypicontents pypi --help

    usage: pypicontents pypi [options]

    General Options:
      -V, --version         Print version and exit.
      -h, --help            Show this help message and exit.

    Pypi Options:
      -l <level>, --loglevel <level>
                            Logger verbosity level (default: INFO). Must be one
                            of: DEBUG, INFO, WARNING, ERROR or CRITICAL.
      -f <path>, --logfile <path>
                            A path pointing to a file to be used to store logs.
      -o <path>, --outputfile <path>
                            A path pointing to a file that will be used to store
                            the JSON Module Index (required).
      -R <letter/number>, --letter-range <letter/number>
                            An expression representing an alphanumeric range to be
                            used to filter packages from PyPI (default: 0-z). You
                            can use a single alphanumeric character like "0" to
                            process only packages beginning with "0". You can use
                            commas use as a list o dashes to use as an interval.
      -L <size>, --limit-log-size <size>
                            Stop processing if log size exceeds <size> (default:
                            3M).
      -M <size>, --limit-mem <size>
                            Stop processing if process memory exceeds <size>
                            (default: 2G).
      -T <sec>, --limit-time <sec>
                            Stop processing if process time exceeds <sec>
                            (default: 2100).

pypicontents stdlib
~~~~~~~~~~~~~~~~~~~

This command generates a JSON Module Index from the Python Standard Library. Read below for more information
on how to use it::

    $ pypicontents stdlib --help

    usage: pypicontents stdlib [options]

    General Options:
      -V, --version         Print version and exit.
      -h, --help            Show this help message and exit.

    Stdlib Options:
      -o <path>, --outputfile <path>
                            A path pointing to a file that will be used to store
                            the JSON Module Index (required).
      -p <version>, --pyver <version>
                            Python version to be used for the Standard Library
                            (default: 2.7).

pypicontents stats
~~~~~~~~~~~~~~~~~~

This command gathers statistics from the logs generated by the ``pypi`` command. Read below for more information
on how to use it::

    $ pypicontents stats --help

    usage: pypicontents stats [options]

    General Options:
      -V, --version         Print version and exit.
      -h, --help            Show this help message and exit.

    Stats Options:
      -i <path>, --inputdir <path>
                            A path pointing to a directory containing JSON files
                            generated by the pypi command (required).
      -o <path>, --outputfile <path>
                            A path pointing to a file that will be used to store
                            the statistics (required).

pypicontents errors
~~~~~~~~~~~~~~~~~~~

This command summarizes errors found in the logs generated by the ``pypi`` command. Read below for more information
on how to use it::

    $ pypicontents errors --help

    usage: pypicontents errors [options]

    General Options:
      -V, --version         Print version and exit.
      -h, --help            Show this help message and exit.

    Errors Options:
      -i <path>, --inputdir <path>
                            A path pointing to a directory containing JSON files
                            generated by the pypi command (required).
      -o <path>, --outputfile <path>
                            A path pointing to a file that will be used to store
                            the errors (required).

pypicontents merge
~~~~~~~~~~~~~~~~~~

This command searches for JSON files generated by the ``pypi`` or ``stdlib`` commands and combines them into one.
Read below for more information on how to use it::

    $ pypicontents merge --help

    usage: pypicontents merge [options]

    General Options:
      -V, --version         Print version and exit.
      -h, --help            Show this help message and exit.

    Merge Options:
      -i <path>, --inputdir <path>
                            A path pointing to a directory containing JSON files
                            generated by pypi or stdlib commands (required).
      -o <path>, --outputfile <path>
                            A path pointing to a file that will be used to store
                            the merged JSON files (required).

About the Module Index
----------------------

.. _Travis: https://travis-ci.org/LuisAlejandro/pypicontents
.. _pypi.json: https://github.com/LuisAlejandro/pypicontents/blob/contents/pypi.json

In the `pypi.json`_ file (located in the ``contents`` branch) you will find a dictionary with all the packages registered
at the main PyPI instance, each one with the following information::

    {
        "pkg_a": {
            "version": [
                "X.Y.Z"
            ],
            "modules": [
                "module_1",
                "module_2",
                "..."
            ],
            "cmdline": [
                "path_1",
                "path_2",
                "..."
            ]
        },
        "pkg_b": {
             "...": "..."
        },
        "...": {},
        "...": {}
    }

This index is generated using Travis_. This is done by executing the ``setup.py`` file
of each package through a monkeypatch that allows us to read the parameters that were passed
to ``setup()``. Check out ``pypicontents/api/process.py`` for more info.

Use cases
~~~~~~~~~

.. _Pip Sala Bim: https://github.com/LuisAlejandro/pipsalabim

* Search which package (or packages) contain a python module. Useful to determine a project's ``requirements.txt`` or ``install_requires``.

::

    import json
    import urllib2
    from pprint import pprint

    pypic = 'https://raw.githubusercontent.com/LuisAlejandro/pypicontents/contents/pypi.json'

    f = urllib2.urlopen(pypic)
    pypicontents = json.loads(f.read())

    def find_package(contents, module):
        for pkg, data in contents.items():
            for mod in data['modules']:
                if mod == module:
                    yield {pkg: data['modules']}

    # Which package(s) content the 'django' module?
    # Output: 
    pprint(list(find_package(pypicontents, 'django')))

..

    Hint: Check out `Pip Sala Bim`_.

Known Issues
~~~~~~~~~~~~

#. Some packages have partial or totally absent data because of some of these
   reasons:

    #. Some packages depend on other packages outside of ``stdlib``. We try to
       override these imports but if the setup heavily depends on it, it will fail anyway.
    #. Some packages are broken and error out when executing ``setup.py``.
    #. Some packages are empty or have no releases.

#. If a package gets updated on PyPI and the change introduces or deletes
   modules, then it won't be reflected until the next index rebuild. You
   should check for the ``version`` field for consistency. Also, if you need a
   more up-to-date index, feel free to download this software and build your own
   index.

Getting help
============

.. _Gitter Chat: https://gitter.im/LuisAlejandro/pypicontents
.. _StackOverflow: http://stackoverflow.com/questions/ask

If you have any doubts or problems, suscribe to our `Gitter Chat`_ and ask for help. You can also
ask your question on StackOverflow_ (tag it ``pypicontents``) or drop me an email at luis@huntingbears.com.ve.

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

.. _COPYING.rst: COPYING.rst
.. _AUTHORS.rst: AUTHORS.rst
.. _GPL-3 License: LICENSE.rst

Copyright 2016-2017, PyPIContents Developers (read AUTHORS.rst_ for a full list of copyright holders).

Released under a `GPL-3 License`_ (read COPYING.rst_ for license details).

Made with :heart: and :hamburger:
=================================

.. image:: http://huntingbears.com.ve/static/img/site/banner.svg

.. _Patreon: https://www.patreon.com/luisalejandro
.. _Flattr: https://flattr.com/profile/luisalejandro
.. _PayPal: https://www.paypal.me/martinezfaneyth
.. _LuisAlejandroTwitter: https://twitter.com/LuisAlejandro
.. _LuisAlejandroGitHub: https://github.com/LuisAlejandro
.. _huntingbears.com.ve: http://huntingbears.com.ve

|

My name is Luis (`@LuisAlejandro`__) and I'm a Free and
Open-Source Software developer living in Maracay, Venezuela.

__ LuisAlejandroTwitter_

If you like what I do, please support me on Patreon_, Flattr_, or donate via PayPal_,
so that I can continue doing what I love.

    Blog huntingbears.com.ve_ · GitHub `@LuisAlejandro`__ · Twitter `@LuisAlejandro`__

__ LuisAlejandroGitHub_
__ LuisAlejandroTwitter_

|
|
