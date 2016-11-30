FROM luisalejandro/debian:sid
MAINTAINER Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>

COPY build-image.sh /usr/share/internal/pypicontents/
RUN bash /usr/share/internal/pypicontents/build-image.sh

ENV PATH=/usr/local/bin:$PATH GPG_KEY=97FC712E4C024BBEA48A61ED3A5CA953F73C700D
    PYTHON_VERSION=3.4.5 PYTHON_PIP_VERSION=9.0.1