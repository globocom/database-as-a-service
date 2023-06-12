FROM python:2.7

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