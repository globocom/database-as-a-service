
.PHONY: default clean pip test run

define CHECK_SCRIPT
import sys
if sys.getdefaultencoding() != "utf-8":
	print "Configure python default encoding to UTF-8"
	sys.exit(1)
endef
export CHECK_SCRIPT

default:
	@cat Makefile | egrep '[a-z]+:' | grep -v 'default:' | egrep --color=never "^[a-z]+"

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


pip: check_environment # install pip libraries
	@pip install -r requirements.txt
	@pip install -r requirements_test.txt

compile:
	@find . -name "*.py" -exec python -m py_compile {} +

db_drop_and_create: db_drop db_create  # drop and create database

db_drop: # drops database
ifeq ($(DBAAS_DATABASE_HOST),)
	@mysql -uroot -e "DROP DATABASE IF EXISTS dbaas"
else
	@mysql -uroot -e "DROP DATABASE IF EXISTS dbaas" -h$(DBAAS_DATABASE_HOST)
endif
db_create: # creates database
ifeq ($(DBAAS_DATABASE_HOST),)
	@mysqladmin -uroot create dbaas
else
	@mysqladmin -uroot create dbaas -h$(DBAAS_DATABASE_HOST)
endif
	@cd dbaas && python manage.py syncdb --migrate --noinput
	@echo "\n\n---------- Creating admin user..."
	@cd dbaas && python manage.py createsuperuser --username='admin' --email='admin@admin.com'

physical_migrate: # create migration to physical app
	@cd dbaas && python manage.py schemamigration physical --auto

tsuru_migrate: # create migration to tsuru app
	@cd dbaas && python manage.py schemamigration tsuru --auto

logical_migrate: # create migration to logical app
	@cd dbaas && python manage.py schemamigration logical --auto

run_migrate: # run all migrations
	@cd dbaas && python manage.py syncdb --migrate --noinput

graph_models: # generate graph models
	@cd dbaas && python manage.py graph_models -g physical logical tsuru > ~/dbaas_model.dot

test: # run tests
ifeq ($(DBAAS_DATABASE_HOST),)
	@mysql -uroot -e "DROP DATABASE IF EXISTS test_dbaas"
else
	@mysql -uroot -e "DROP DATABASE IF EXISTS test_dbaas" -h$(DBAAS_DATABASE_HOST)
endif

	@cd dbaas && python manage.py test $(filter-out $@,$(MAKECMDGOALS))

run: # run local server
	@cd dbaas && python manage.py runserver 0.0.0.0:8000 $(filter-out $@,$(MAKECMDGOALS))

shell: # run django shell
	@cd dbaas && python manage.py shell_plus --use-pythonrc

update_permissions:
	@cd dbaas && python manage.py update_permissions

fix_user_roles_permissions: #Fix user roles permissions
	@cd dbaas && python manage.py fix_user_roles_permissions
