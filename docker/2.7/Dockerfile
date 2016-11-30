FROM luisalejandro/debian:sid
MAINTAINER Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>

COPY build-image.sh /usr/share/internal/pypicontents/
RUN bash /usr/share/internal/pypicontents/build-image.sh

ENV PATH=/usr/local/bin:$PATH GPG_KEY=C01E1CAD5EA2C4F0B8E3571504C367C218ADD4FF
    PYTHON_VERSION=2.7.12 PYTHON_PIP_VERSION=9.0.1