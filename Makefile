
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

docker_build:
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
	@cp requirements* dev/. && cd dev && docker build -t dbaas_dev .

dev_docker_setup:
	@cd dev && ./setup_db.sh $(filter-out $@,$(MAKECMDGOALS))

dev_docker_manage: # execute manage.py commands
	@cd dev && docker-compose run app /code/dbaas/manage.py $(filter-out $@,$(MAKECMDGOALS))

dev_docker_migrate:
	@cd dev && docker-compose run app /code/dbaas/manage.py migrate

dev_docker_mysql_shell:
	@cd dev && docker-compose exec dev_mysqldb57 bash -c "mysql dbaas -u root -p123"

dev_docker_run:
	@cd dev && docker-compose up

dev_docker_django_shell: # run django shell
	@cd dev && docker-compose exec app /code/dbaas/manage.py shell_plus --use-pythonrc

dev_docker_app_shell:
	@cd dev && docker-compose exec app bash

dev_docker_stop:
	@cd dev && docker-compose down

dev_docker_generate_migration:
	$(eval app = $(if $(app),$(app),$(error Modo de uso: make dev_docker_generate_migration app=NOME_DA_APP)))
	@cd dev && docker-compose run app /code/dbaas/manage.py schemamigration ${app} --auto

dev_docker_restart:
	@cd dev && docker-compose restart $(filter-out $@,$(MAKECMDGOALS))

dev_docker_develop_package:
	@cd dev && docker-compose exec app bash /code/dev/debug_lib.sh $(filter-out $@,$(MAKECMDGOALS))
	@cd dev && docker-compose exec -u root app_celery bash /code/dev/debug_lib.sh $(filter-out $@,$(MAKECMDGOALS))
	@make dev_docker_restart app
	@make dev_docker_restart app_celery
%:
	@: