FROM python:2.7.9-slim

# Python optimization to run on docker
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list


# waiting for redhat bugfix
# https://discuss.circleci.com/t/failed-to-fetch-jessie-updates/29246
# RUN rm /etc/apt/sources.list
# RUN echo "deb http://security.debian.org/debian/ jessie-backports main" | tee -a /etc/apt/sources.list
# RUN echo "deb-src http://security.debian.org/debian/ jessie-backports main" | tee -a /etc/apt/sources.list
# RUN echo "Acquire::Check-Valid-Until false;" | tee -a /etc/apt/apt.conf.d/10-nocheckvalid
# RUN echo 'Package: *\nPin: origin "security.debian.org"\nPin-Priority: 500' | tee -a /etc/apt/preferences.d/10-archive-pin
# RUN echo "deb [check-valid-until=no] http://cdn-fastly.deb.debian.org/debian jessie main" > /etc/apt/sources.list.d/jessie.list
# RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/jessie-backports.list
# RUN sed -i '/deb http:\/\/deb.debian.org\/debian jessie-updates main/d' /etc/apt/sources.list
# RUN apt-get -o Acquire::Check-Valid-Until=false update

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


# Not sure what this does......... TODO test if needed?
# RUN sed '/st_mysql_options options;/a unsigned int reconnect;' /usr/include/mysql/mysql.h -i.bkp

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

# User, home, and app basics
RUN useradd --create-home app
WORKDIR /home/app
USER app

COPY . .

ARG build_info
RUN echo ${build_info} > build_info.txt

# RUN nc -lU /dev/log
# RUN mkdir /dev
USER root

RUN touch /dev/log
USER app

ENTRYPOINT [ "./gunicorn.sh" ]