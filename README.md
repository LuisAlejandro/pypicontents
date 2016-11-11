# PyPIContents

> Because we need a content index for pip

[![Build Status](https://travis-ci.org/LuisAlejandro/pypicontents.svg?branch=master)](https://travis-ci.org/LuisAlejandro/pypicontents)

This project aims to (sort of) mimic what the [Contents file](https://www.debian.org/distrib/packages#search_contents) means for a Debian
based package repository, but for the PyPI.

It works by generating a content index instead of just a package index. In the
file [contents.json](https://github.com/LuisAlejandro/pypicontents/blob/contents/contents.json)
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

pypic = 'https://raw.githubusercontent.com/LuisAlejandro/pypicontents/contents/contents.json'

f = urllib2.urlopen(pipyc)
pypicontents = json.loads(f.read())

def find_package(contents, module):
    for pkg, data in contents.items():
        for mod in data['modules']:
            if mod == module:
                yield pkg

# Which package(s) content the 'ldap' module?
# Output: 
print list(find_package(pypicontents, 'ldap'))

# Which package(s) content the 'numpy' module?
# Output: 
print list(find_package(pypicontents, 'numpy'))
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