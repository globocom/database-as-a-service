
.PHONY: default clean pip test run

define CHECK_SCRIPT
import sys
if sys.getdefaultencoding() != "utf-8":
	print "Configure python default encoding to UTF-8"
	sys.exit(1)
endef
export CHECK_SCRIPT

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
	$(eval model = $(if $(model),$(model),$(error Modo de uso: make generate_migration model=NOME_DO_MODEL)))
	@cd dbaas && python manage.py schemamigration ${model} --auto

graph_models: # generate graph models
	@cd dbaas && python manage.py graph_models -g physical logical tsuru > ~/dbaas_model.dot

dev_mode:
	@sed -i "" -e "/check_dns(/s/^/#/" dbaas/workflow/steps/util/deploy/check_dns.py
