FROM python:2.7

ADD . /code
WORKDIR /code
RUN apt-get update
RUN apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev mysql-client
RUN easy_install ipython==5.1.0 ipdb==0.10.1
RUN pip install -U pip
RUN pip install -r requirements_test.txt
ENTRYPOINT /code/tests.sh
