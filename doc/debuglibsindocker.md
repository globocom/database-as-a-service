## To debug DBAAS libs using docker follow this steps

- The libs root path must be tha same than DBaaS project root path, like ˜/Users/[USERNAME]/projects˜.

To enable lib debug run the following command:
   $make dev_docker_develop_package [package_name] # (example: make dev_docker_develop_package dbaas-aclapi)

With this command the source package in docker imnage will be the host machine package repo until you run a new docker image build.