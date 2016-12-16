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

.. image:: https://landscape.io/github/LuisAlejandro/pypicontents/master/landscape.svg?style=flat
   :target: https://landscape.io/github/LuisAlejandro/pypicontents/master
   :alt: Landscape

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

PyPIContents generates a configurable index written in `JSON` format that serves as a database for applications
like `pipsalabim`_. It can be 

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

Usage
-----


Using the Index
---------------

# PyPIContents

> Because we need a content index for pip

[![Build Status](https://travis-ci.org/LuisAlejandro/pypicontents.svg?branch=master)](https://travis-ci.org/LuisAlejandro/pypicontents)

This project aims to (sort of) mimic what the [Contents file](https://www.debian.org/distrib/packages#search_contents) means for a Debian
based package repository, but for the PyPI.

It works by generating a content index instead of just a package index. In the
file [pypi.json](https://github.com/LuisAlejandro/pypicontents/blob/contents/pypi.json)
you will find a dictionary with all the packages registered at the main PyPI instance,
each one with the following information:

```json
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
```

This index is generated using [Travis](https://travis-ci.org/LuisAlejandro/pypicontents). It's done by executing the setup.py of each package through a monkeypatch that allows us to read the parameters that were passed to `setup()`, and then we get `modules`, `cmdline`. Checkout `pypicontents/process.py` for more info.


### Use cases

* Search which package (or packages) contain a python module. Useful to determine a project's `requirements.txt` or `install_requires`.

```python
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
```

> Hint: Use a module finder tool like [snakefood](https://bitbucket.org/blais/snakefood) or [modulefinder](https://docs.python.org/2/library/modulefinder.html) to search for imports in your project, then use pypicontents to search which packages contain them.


### Known Issues

* Some packages have partial or totally absent data because of some of these
  reasons:
    1. Some packages depend on other packages outside of `stdlib`. We try to
       override these imports but if the setup heavily depends on it, it will fail anyway.
    2. Some packages are broken and error out when executing `setup.py`.
    3. Some packages are empty or have no releases.
* If a package gets updated on PyPI and the change introduces or deletes
  modules, then it won't be reflected until the next index rebuild. You
  should check for the `version` field for consisntency. Also, if you need a
  more up-to-date index, feel free to download this software and build your own
  index.

### License

See [COPYING](COPYING.md) for details.


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

Copyright 2016, PyPIContents Developers (read AUTHORS.rst_ for a full list of copyright holders).

Released under a `GPL-3 License`_ (read COPYING.rst_ for license details).

Made with :heart: and :hamburger:
=================================

.. image:: http://huntingbears.com.ve/static/img/site/banner.svg

.. _Patreon: https://www.patreon.com/luisalejandro
.. _Flattr: https://flattr.com/profile/luisalejandro
.. _PayPal: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=B8LPXHQY8QE8Y
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
