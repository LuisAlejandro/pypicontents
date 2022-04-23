FROM dockershelf/python:3.10
LABEL maintainer "Luis Alejandro Martínez Faneyth <luis@collagelabs.org>"

RUN apt-get update && \
    apt-get install sudo python3.10-venv git

RUN ln -s /usr/bin/python3.10 /usr/bin/python

ADD requirements.txt requirements-dev.txt /root/
RUN pip3 install -r /root/requirements.txt -r /root/requirements-dev.txt
RUN rm -rf /root/requirements.txt /root/requirements-dev.txt

RUN useradd -ms /bin/bash luisalejandro
RUN echo "luisalejandro ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/luisalejandro
USER luisalejandro
WORKDIR /home/luisalejandro/app

CMD tail -f /dev/null