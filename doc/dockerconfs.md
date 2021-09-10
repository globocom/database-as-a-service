## To debug DBAAS libs using docker follow this steps

- The libs root path must be tha same than DBaaS project root path, like ˜/Users/[USERNAME]/projects˜.

To enable lib debug run the following command:
   $make dev_docker_develop_package [package_name] # (example: make dev_docker_develop_package dbaas-aclapi)

With this command the source package in docker imnage will be the host machine package repo until you run a new docker image build.

You can edit/remove libs that are in debug mode manually. Just edit the file: dev/debug_lib/lib.list

## to use cert files

Docker compose already map the SSL certs path to container.

Just add your certificate files to /etc/ssl/certs in host machine and then it will be available in /etc/ssl/certsg path in docker container app and app_celery