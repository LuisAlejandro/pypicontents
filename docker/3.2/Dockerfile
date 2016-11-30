FROM luisalejandro/debian:sid
MAINTAINER Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>

COPY build-image.sh /usr/share/internal/pypicontents/
RUN bash /usr/share/internal/pypicontents/build-image.sh

ENV PATH=/usr/local/bin:$PATH GPG_KEY=26DEA9D4613391EF3E25C9FF0A5B101836580288
    PYTHON_VERSION=3.2.6 PYTHON_PIP_VERSION=9.0.1