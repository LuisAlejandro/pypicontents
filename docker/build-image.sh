#!/bin/bash

export GNUPGHOME="$(mktemp -d)"

DPKG_BUILD_DEPENDS="gcc \
                    libbz2-dev \
                    libc6-dev \
                    libgdbm-dev \
                    liblzma-dev \
                    libncurses-dev \
                    libreadline-dev \
                    libsqlite3-dev \
                    libssl-dev \
                    make \
                    tcl-dev \
                    tk-dev \
                    wget \
                    xz-utils \
                    zlib1g-dev"
DPKG_DEPENDS="ca-certificates \
              libgdbm3 \
              libsqlite3-0 \
              libssl1.0.0"

# Install dependencies
apt-get update
apt-get install ${DPKG_DEPENDS} ${DPKG_BUILD_DEPENDS}

wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz"
wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc"

gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY"
gpg --batch --verify python.tar.xz.asc python.tar.xz

mkdir -p /usr/src/python
tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz
rm -rf "$GNUPGHOME" python.tar.xz.asc python.tar.xz

cd /usr/src/python
./configure --enable-loadable-sqlite-extensions --enable-shared
make -j$(nproc)
make install
ldconfig

if [ ! -e /usr/local/bin/pip3 ]; then
    wget -O /tmp/get-pip.py 'https://bootstrap.pypa.io/get-pip.py'
    python3 /tmp/get-pip.py "pip==$PYTHON_PIP_VERSION"
    rm /tmp/get-pip.py
fi

# we use "--force-reinstall" for the case where the version of pip we're trying to install is the same as the version bundled with Python
# ("Requirement already up-to-date: pip==8.1.2 in /usr/local/lib/python3.6/site-packages")
# https://github.com/docker-library/python/pull/143#issuecomment-241032683
pip3 install --no-cache-dir --upgrade --force-reinstall "pip==$PYTHON_PIP_VERSION"

# make some useful symlinks that are expected to exist
cd /usr/local/bin
[ -e easy_install ] || ln -s easy_install-* easy_install
ln -s idle3 idle
ln -s pydoc3 pydoc
ln -s python3 python
ln -s python3-config python-config

apt-get purge ${PKG_BUILD_DEPENDS}
apt-get autoremove

find /usr/local -depth \
    \( \
        \( -type d -a -name test -o -name tests \) \
        -o \
        \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    \) -exec rm -rf '{}' +

# Final cleaning
rm -rf /usr/src/python ~/.cache
find /tmp -type f -print0 | xargs -0r rm -rf
find /var/tmp -type f -print0 | xargs -0r rm -rf
find /var/log -type f -print0 | xargs -0r rm -rf
find /var/lib/apt/lists -type f -print0 | xargs -0r rm -rf
