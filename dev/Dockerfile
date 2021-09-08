FROM python:2.7
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND "noninteractive apt-get install PACKAGE"
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN  useradd -ms /bin/bash python && \
     chown -R python: /code && \
     apt-get update && \
     apt-get install -y --no-install-recommends \
             python-pip \
             build-essential \
             libsasl2-dev \
             python-dev \
             libldap2-dev \
             libssl-dev \
             default-libmysqlclient-dev \
             gcc \
     && rm -rf /var/lib/apt/lists/* \
     && sed '/st_mysql_options options;/a unsigned int reconnect;' /usr/include/mysql/mysql.h -i.bkp \
     && pip install --upgrade pip \
     && pip install ipython==5.1.0 \
     && pip install ipdb==0.10.1 \
     && pip install -r requirements_test.txt \
     && chown -R python: /usr/local/lib/python2.7/