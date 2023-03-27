FROM debian:stretch-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        python2.7 \
        python2.7-dev \
        python-pip \
        python-setuptools \
        python-wheel \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND "noninteractive apt-get install PACKAGE"
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir /code
WORKDIR /code

RUN  useradd -ms /bin/bash python && \
     chown -R python: /code && \
     chown -R python: /usr/local/lib/python2.7/

# Maybe run upgrade as well???
RUN apt-get update

# So we can install stuff that compiles with gcc
RUN apt-get install -y python-dev --force-yes
RUN apt-get install -y build-essential --force-yes

# Nice to have
RUN apt-get install -y nano --force-yes
RUN apt-get install -y htop --force-yes
RUN apt-get install -y vim --force-yes
RUN apt-get install -y ncdu --force-yes
RUN apt install -y --force-yes curl

# So we can install mysql libs properly
RUN apt install -y --force-yes libmysqlclient-dev

# So we can install LDAP
RUN apt install -y --force-yes python-ldap
RUN apt install -y --force-yes libldap2-dev
RUN apt install -y --force-yes libsasl2-dev
RUN apt install -y --force-yes libssl-dev
RUN apt install -y --force-yes mysql-client
RUN apt install -y --force-yes telnet

# If we dont upgrade pip to a smaller version, it just give an error when trying to do the upgrade.
RUN pip install --upgrade pip==9.0.1
RUN pip install --upgrade pip
RUN pip install ipython==5.1.0
RUN pip install ipdb==0.10.1
RUN pip install -U setuptools
RUN pip install --upgrade distribute

# RUN export CFLAGS="-I$(xcrun --show-sdk-path)/usr/include/sasl"
RUN pip install python-ldap

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://artifactory.globoi.com/artifactory/api/pypi/pypi-all/simple/ -r requirements.txt

ADD . /code/