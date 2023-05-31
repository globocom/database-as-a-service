include .env

.PHONY: default clean pip test run

define CHECK_SCRIPT
import sys
if sys.getdefaultencoding() != "utf-8":
	print "Configure python default encoding to UTF-8"
	sys.exit(1)
endef
export CHECK_SCRIPT

export PWD=$(shell pwd)
export PROJECT_PATH=$(shell dirname $$PWD)


# Use make -e DBAAS_DATABASE_HOST=another_host to replace default value		 

default:
	@awk -F\: '/^[a-z_]+:/ && !/default/ {printf "- %-20s %s\n", $$1, $$2}' Makefile

# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
#
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))


clean: # remove temporary files
	@find . -name \*.pyc -delete
	@find . -name \*.orig -delete
	@find . -name \*.bak -delete
	@find . -name __pycache__ -delete
	@find . -name coverage.xml -delete
	@find . -name test-report.xml -delete
	@find . -name .coverage -delete


check_environment: # check if your local environment is ok to running this project
	@echo "$$CHECK_SCRIPT" | python -


pip: # install pip libraries
	@pip install -r requirements.txt
	@pip install -r requirements_test.txt


compile:
	@find . -name "*.py" -exec python -m py_compile {} +


db_reset: # drop and create database
	@mysqladmin -uroot -p$(DBAAS_DATABASE_PASSWORD) -f drop dbaas -hlocalhost; true
	@mysqladmin -uroot -p$(DBAAS_DATABASE_PASSWORD) create dbaas -hlocalhost
	@cd dbaas && python manage.py syncdb --migrate --noinput


load_basic_roles: # load roles
	@cd dbaas && python manage.py loaddata basic_roles.yaml


load_basic_configs: # load roles
	@cd dbaas && python manage.py loaddata basic_configs.yaml


reset_data: db_reset # drop and create database and insert sample data
	@cd dbaas && python manage.py sample_data
	@cd dbaas && python manage.py loaddata basic_roles.yaml
	@cd dbaas && python manage.py loaddata basic_configs.yaml


run_migrate: # run all migrations
	@cd dbaas && python manage.py syncdb --migrate --noinput --no-initial-data
	@cd dbaas && python manage.py update_permissions

test: # run tests
	@cd dbaas && python manage.py test --settings=dbaas.settings_test --traceback $(filter-out $@,$(MAKECMDGOALS))

unit_test: # run tests
	@cd dbaas && REUSE_DB=1 coverage run --source='.' manage.py test --settings=dbaas.settings_test --traceback $(filter-out $@,$(MAKECMDGOALS)) && coverage xml

send_codecov:
	@cd dbaas && curl -s https://codecov.io/bash > codecov.sh  && bash codecov.sh 

docker_build_test:
	docker build -t dbaas_test .

test_with_docker:
	docker-compose run test

docker_mysql_55:
	docker-compose run --publish="3306:3306" mysqldb55

docker_mysql_56:
	docker-compose run --publish="3306:3306" mysqldb56

docker_mysql_57:
	docker-compose run --publish="3306:3306" mysqldb57

kill_mysql:
	@ps aux | grep mysqldb | grep -v 'grep mysqldb' | awk '{print $$2}' | xargs kill

run: # run local server
	@cd dbaas && python manage.py runserver 0.0.0.0:8000 $(filter-out $@,$(MAKECMDGOALS))

run_celery_debug: # run local celery
	@cd dbaas && CELERY_RDBSIG=1 celery worker -E --loglevel=DEBUG --app=dbaas --beat $(filter-out $@,$(MAKECMDGOALS))

run_celery: # run local celery
	@cd dbaas && celery worker -E --loglevel=DEBUG --app=dbaas --beat $(filter-out $@,$(MAKECMDGOALS))

sync_celery: # sync celery tasks
	@cd dbaas && python manage.py sync_celery --celery_hosts=1

shell: # run django shell
	@cd dbaas && python manage.py shell_plus --use-pythonrc

update_permissions:
	@cd dbaas && python manage.py update_permissions

generate_migration:
	$(eval app = $(if $(app),$(app),$(error Modo de uso: make generate_migration app=NOME_DA_APP)))
	@cd dbaas && python manage.py schemamigration ${app} --auto

graph_models: # generate graph models
	@cd dbaas && python manage.py graph_models -g physical logical tsuru > ~/dbaas_model.dot

dev_mode:
	@sed -i "" -e "/check_dns(/s/^/#/" dbaas/workflow/steps/util/deploy/check_dns.py

migrate:
	@cd dbaas && python manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

dev_docker_build:
	@cp requirements.txt dev/. && cd dev && docker build -t dbaas_dev .

dev_docker_setup:
	@cd dev && ./setup_db.sh $(filter-out $@,$(MAKECMDGOALS))

dev_docker_manage: # execute manage.py commands
	@cd dev && docker-compose run app /code/dbaas/manage.py $(filter-out $@,$(MAKECMDGOALS))

dev_docker_migrate:
	@cd dev && docker-compose run app /code/dbaas/manage.py migrate

dev_docker_mysql_shell:
	@cd dev && docker-compose exec dev_mysqldb57 bash -c "mysql dbaas -u root -p123"

dev_docker_redis_shell:
	@cd dev && docker-compose exec dev_redisdb bash -c "redis-cli"

dev_docker_run:
	@cd dev && docker-compose up

dev_docker_django_shell: # run django shell
	@cd dev && docker-compose exec app /code/dbaas/manage.py shell_plus --use-pythonrc

dev_docker_app_shell:
	@cd dev && docker-compose exec app bash

dev_docker_app_celery_shell:
	@cd dev && docker-compose exec app_celery bash

dev_docker_stop:
	@cd dev && docker-compose down

dev_docker_generate_migration:
	$(eval app = $(if $(app),$(app),$(error Modo de uso: make dev_docker_generate_migration app=NOME_DA_APP)))
	@cd dev && docker-compose run app /code/dbaas/manage.py schemamigration ${app} --auto

dev_docker_restart:
	@cd dev && docker-compose restart $(filter-out $@,$(MAKECMDGOALS))

dev_docker_develop_package:
	@cd dev && docker-compose exec app bash /code/dev/add_debug_lib.sh $(filter-out $@,$(MAKECMDGOALS))
	@make dev_docker_restart app app_celery
%:
	@:


docker_run:
	# make docker_stop 
	# docker stop dbaas_app 2>&1 >/dev/null
	# docker rm dbaas_app 2>&1 >/dev/null
	# docker run --log-driver syslog --name=dbaas_app -e "PORT=80" -e "WORKERS=2"  -p 80:80 dbaas/dbaas_app 
	docker run --name=dbaas_app \
		-v /Users/marcelo.soares/dbaas_dev_pki/pki/globocom:/etc/pki/globocom \
		-e "PORT=80" \
		-e "WORKERS=2" \
		-e "DBAAS_DATABASE_HOST=dbaas-01-145632598674.dev.mysql.globoi.com" \
		-e "DBAAS_DATABASE_USER=u_dbaas" \
		-e "DBAAS_DATABASE_NAME=dbaas" \
		-e "DBAAS_DATABASE_PASSWORD=u3umvWZ7LM" \
		-e "REDIS_HOST=dbaas.dev.redis.globoi.com" \
		-e "REDIS_PASSWORD=dfghg3vsdb6dbBSD1" \
		-e "REDIS_DB=0" \
		-e "REDIS_PORT=6379" \
		-e "DBAAS_OAUTH2_LOGIN_ENABLE=1" \
		-e "ALLACCESS_CREATE_RANDOM_USER=0" \
		-e "DBAAS_LDAP_ENABLED="1" \
		-e "DBAAS_LDAP_CERTDIR="/etc/pki/globocom/" \
		-e "DBAAS_LDAP_CACERTFILE="glb_cacert.pem" \
		-e "DBAAS_LDAP_CERTFILE="glb_clientcrt.pem" \
		-e "DBAAS_LDAP_KEYFILE="glb_clientkey.pem" \
		-e "AUTH_LDAP_SERVER_URI="ldaps://ldap.globoi.com:636" \
		-e "AUTH_LDAP_BIND_DN="cn=gerenciasenha,ou=Usuarios,dc=globoi,dc=com" \
		-e "AUTH_LDAP_BIND_PASSWORD="glb!ldap..," \
		-e "AUTH_LDAP_USER_SEARCH="ou=Usuarios,dc=globoi,dc=com" \
		-e "AUTH_LDAP_GROUP_SEARCH="ou=Grupos,dc=globoi,dc=com" \
		-e "DBAAS_NOTIFICATION_BROKER_URL=redis://:dfghg3vsdb6dbBSD1@dbaas.dev.redis.globoi.com:6379/0" \
		-e "DBAAS_DJ_SECRET_KEY=n3#i=z^st83t5-k_xw!v9t_ey@h=!&6!3e$l6n&sn^o9@f&jxv" \
		-p 80:80 dbaas/dbaas_app 




docker_stop:
	docker stop dbaas_app


# a gcp possui mais de um env
# para acessar os secrets corretos, garantimos que estamos no projeto correto
set_env:
	@echo "Project env:${PROJECT_ENV}"; \
	if [ "${PROJECT_ENV}" = "DEV" ]; then \
    	echo 'changing project to DEV'; \
    	LOWERCASE_ENV="dev"; \
    	gcloud config set project gglobo-dbaaslab-dev-qa; \
		exit 0; \
	elif [ "${PROJECT_ENV}" = "PROD" ]; then \
		echo 'changing project to PROD'; \
		LOWERCASE_ENV="prod"; \
		gcloud config set project gglobo-dbaas-hub; \
		exit 0; \
	else\
		echo "PROJECT_ENV not found. Exiting";\
		echo "please call like this: make set_env PROJECT_ENV=PROD or DEV";\
		exit 1;\
	fi\

get_last_tag:
	@echo "exemplo de uso make get_last_tag ENV=DEV"; \
	echo "exemplo de uso make get_last_tag ENV=PROD"; \
	make set_env PROJECT_ENV=${ENV}; \
	SECRET_NAME="DBDEV_${ENV}_DBAAS_IMAGE_VERSION"; \
	echo "Getting secret $${SECRET_NAME}"; \
	gcloud secrets versions access "latest" --secret "$${SECRET_NAME}"; \
	echo " " 
	
set_new_tag:
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make set_tag TAG=v1.02 ENV=DEV"
	@echo "exemplo de uso make set_tag TAG=v1.034 ENV=PROD"
	@make set_env PROJECT_ENV=${ENV}; \
	if [ $$? -eq 0 ]; then \
		echo "env set"; \
	else \
		echo "ERROR SETTING ENVIRONMENT"; \
		exit 1; \
	fi; \
	SECRET=${TAG}; \
	SECRET_NAME="DBDEV_${ENV}_DBAAS_IMAGE_VERSION"; \
	echo "$${SECRET_NAME}"; \
	echo "$${SECRET}" | gcloud secrets create "$${SECRET_NAME}" --locations=us-east1,southamerica-east1 --replication-policy="user-managed" --labels="app=dbaas-app" --data-file=- ; \
	if [ $$? -eq 0 ]; then \
		echo "Created the new secret sucessfully"; \
	else \
		echo "Secret already exists, updating its version!" ; \
		echo $${SECRET} | gcloud secrets versions add $${SECRET_NAME} --data-file=- ; \
	fi


docker_deploy_gcp:
	@echo "tag usada:${TAG}"
	make docker_deploy_build TAG=${TAG}
	make docker_deploy_push TAG=${TAG}

docker_deploy_build: 
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_build TAG=v1.02"
	GIT_BRANCH=$$(git branch --show-current); \
	GIT_COMMIT=$$(git rev-parse --short HEAD); \
	DATE=$$(date +"%Y-%M-%d_%T"); \
	INFO="date:$$DATE  branch:$$GIT_BRANCH  commit:$$GIT_COMMIT"; \
	docker build . -t us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/dbaas-app:${TAG} \
		--label git-commit=$(git rev-parse --short HEAD) \
		--build-arg build_info="$$INFO"  \
		-f Dockerfile.gcp

docker_deploy_push:
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_push TAG=v1.02"
	docker push us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/dbaas-app:${TAG}

# deploy base docker image
docker_deploy_gcp_base:
	@echo "tag usada:${TAG}"
	make docker_deploy_build_base TAG=${TAG}
	make docker_deploy_push_base TAG=${TAG}

docker_deploy_build_base: 
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_build TAG=v1.02"
	GIT_BRANCH=$$(git branch --show-current); \
	GIT_COMMIT=$$(git rev-parse --short HEAD); \
	DATE=$$(date +"%Y-%M-%d_%T"); \
	INFO="date:$$DATE  branch:$$GIT_BRANCH  commit:$$GIT_COMMIT"; \
	docker build . -t us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/dbaas-base:${TAG} \
		--label git-commit=$(git rev-parse --short HEAD) \
		--build-arg build_info="$$INFO"  \
		-f Dockerfile.base

docker_deploy_push_base:
	@echo "tag usada:${TAG}"
	@echo "exemplo de uso make docker_deploy_push TAG=v1.02"
	docker push us-east1-docker.pkg.dev/gglobo-dbaas-hub/dbaas-docker-images/dbaas-base:${TAG}

# Docker part, for deploy, for GCP
# TODO, standardize with other providers
docker_build:
	GIT_BRANCH=$$(git branch --show-current); \
	GIT_COMMIT=$$(git rev-parse --short HEAD); \
	DATE=$$(date +"%Y-%M-%d_%T"); \
	INFO="date:$$DATE  branch:$$GIT_BRANCH  commit:$$GIT_COMMIT"; \
	docker build -t dbaas/dbaas_app --label git-commit=$(git rev-parse --short HEAD) --build-arg build_info="$$INFO" . -f Dockerfile_gcp

gcp_deploy_dev:
	$(call check_defined, TAG, 'Precisa enviar a TAG=v1.x.x')
	make docker_deploy_gcp ${TAG}
	make set_new_tag TAG=${TAG} ENV=DEV
	make gcp_deploy_dev_script

gcp_deploy_dev_script:
	./scripts/deploy_dev.sh

# Mysql utilities
gcp_mysql_dev_cli:
	make set_env PROJECT_ENV=DEV; \
	HOST=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_HOST"); \
	USER=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_USER"); \
	DB=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_NAME"); \
	PASS=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_PASSWORD"); \
	mysql -u$$USER -p$$PASS -h$$HOST

gcp_mysql_dev_dump:
	make set_env PROJECT_ENV=DEV; \
	HOST=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_HOST"); \
	USER=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_USER"); \
	DB=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_NAME"); \
	PASS=$(shell gcloud secrets versions access "latest" --secret "DBDEV_DEV_DBAAS_DBAAS_DATABASE_PASSWORD"); \
	mysqldump -u$$USER -p$$PASS -h$$HOST -B $$DB --column-statistics=0 --verbose  > ./dbaas_dev_$(shell date +%Y-%m-%d-%H:%M:%S).sql

