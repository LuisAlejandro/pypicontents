FROM luisalejandro/debian:sid
MAINTAINER Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>

COPY build-image.sh /usr/share/internal/pypicontents/
RUN bash /usr/share/internal/pypicontents/build-image.sh

ENV PATH=/usr/local/bin:$PATH GPG_KEY=DBBF2EEBF925FAADCF1F3FFFD9866941EA5BBD71
    PYTHON_VERSION=2.6.9 PYTHON_PIP_VERSION=9.0.1