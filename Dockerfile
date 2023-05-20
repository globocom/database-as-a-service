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

ADD . /code
WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
	libsasl2-dev \
	python-dev \
	libldap2-dev \
	libssl-dev \
	default-libmysqlclient-dev \
	curl \
 && rm -rf /var/lib/apt/lists/*
RUN sed '/st_mysql_options options;/a unsigned int reconnect;' /usr/include/mysql/mysql.h -i.bkp
RUN pip install --upgrade pip \
    && pip install ipython==5.1.0 \
    && pip install ipdb==0.10.1 \
    && pip install -r requirements_test.txt

ENTRYPOINT /code/tests.sh