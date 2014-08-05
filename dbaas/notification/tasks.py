# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings

from system.models import Configuration
from celery.utils.log import get_task_logger
from celery.exceptions import SoftTimeLimitExceeded
from dbaas.celery import app

from util import call_script
from util.decorators import only_one
from util import email_notifications
from util.providers import make_infra
from .util import get_clone_args
from .models import TaskHistory
from drivers import factory_for
from django.db.models import Sum, Count
from physical.models import Plan

from physical.models import DatabaseInfra
from logical.models import Database
from account.models import Team

LOG = get_task_logger(__name__)


def get_history_for_task_id(task_id):
	try:
		return TaskHistory.objects.get(task_id=task_id)
	except Exception, e:
		LOG.error("could not find history for task id %s" % task_id)
		return None


def rollback_database(dest_database):
	dest_database.is_in_quarantine = True
	dest_database.save()
	dest_database.delete()


@app.task(bind=True)
def create_database(self, name, plan, environment, team, project, description, user=None):
	# register History
	task_history = TaskHistory.register(request=self.request, user=user)
	LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
		self.request.id, self.request.task, self.request.kwargs, str(self.request.args)))

	task_history.update_details(persist=True, details="Loading Process...")

	result = make_infra(plan=plan, environment=environment, name=name, task=task_history)

	if result['created']==False:

		if 'exceptions' in result:
			error = "\n".join(": ".join(err) for err in result['exceptions']['error_codes'])
			traceback = "\nException Traceback\n".join(result['exceptions']['traceback'])
			error = "{}\n{}\n{}".format(error, traceback, error)
		else:
			error = "There is not any infra-structure to allocate this database."

		task_history.update_status_for(TaskHistory.STATUS_ERROR, details=error)
		return


	database = Database.provision(name, result['databaseinfra'])
	database.team = team
	database.project = project
	database.description = description
	database.save()
	task_history.update_dbid(db=database)

	task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details='Database created successfully')
	return


@app.task(bind=True)
def clone_database(self, origin_database, clone_name, user=None):
	# register History
	task_history = TaskHistory.register(request=self.request, user=user)

	LOG.info("origin_database: %s" % origin_database)

	dest_database = Database.objects.get(pk=origin_database.pk)
	dest_database.name = clone_name
	dest_database.pk = None

	task_history.update_details(persist=True, details="Loading Process...")
	result = make_infra(plan=origin_database.plan, environment=origin_database.environment, name=clone_name,
	                    task=task_history)

	if result['created']==False:

		if 'exceptions' in result:
			error = "\n\n".join(": ".join(err) for err in result['exceptions']['error_codes'])
			traceback = "\n\nException Traceback\n".join(result['exceptions']['traceback'])
			error = "{}\n{}".format(error, traceback)
		else:
			error = "There is not any infra-structure to allocate this database."

		task_history.update_status_for(TaskHistory.STATUS_ERROR, details=error)
		return

	dest_database.databaseinfra = result['databaseinfra']
	dest_database.save()
	LOG.info("dest_database: %s" % dest_database)

	LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
		self.request.id, self.request.task, self.request.kwargs, str(self.request.args)))

	try:
		args = get_clone_args(origin_database, dest_database)
		script_name = factory_for(origin_database.databaseinfra).clone()
		return_code, output = call_script(script_name, working_dir=settings.SCRIPTS_PATH, args=args, split_lines=False)
		LOG.info("%s - return code: %s" % (self.request.id, return_code))
		if return_code != 0:
			task_history.update_status_for(TaskHistory.STATUS_ERROR, details=output + "\nTransaction rollback")
			LOG.error("task id %s - error occurred. Transaction rollback" % self.request.id)
			rollback_database(dest_database)
		else:
			task_history.update_dbid(db=dest_database)
			task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details=output)
	except SoftTimeLimitExceeded:
		LOG.error("task id %s - timeout exceeded" % self.request.id)
		task_history.update_status_for(TaskHistory.STATUS_ERROR, details="timeout exceeded")
		rollback_database(dest_database)
	except Exception, e:
		LOG.error("task id %s error: %s" % (self.request.id, e))
		task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)
		rollback_database(dest_database)
	return


@app.task
@only_one(key="db_infra_notification_key", timeout=20)
def databaseinfra_notification(self, user=None):
	task_history = TaskHistory.register(request=self.request, user=user)
	threshold_infra_notification = Configuration.get_by_name_as_int("threshold_infra_notification", default=0)
	if threshold_infra_notification <= 0:
		LOG.warning("database infra notification is disabled")
		return

	# Sum capacity per databseinfra with parameter plan, environment and engine
	infras = DatabaseInfra.objects.values('plan__name', 'environment__name', 'engine__engine_type__name',
	                                      'plan__provider').annotate(capacity=Sum('capacity'))
	for infra in infras:
		# total database created in databaseinfra per plan, environment and engine
		used = DatabaseInfra.objects.filter(plan__name=infra['plan__name'],
		                                    environment__name=infra['environment__name'],
		                                    engine__engine_type__name=infra['engine__engine_type__name']).aggregate(
			used=Count('databases'))
		# calculate the percentage
		percent = int(used['used'] * 100 / infra['capacity'])
		if percent >= threshold_infra_notification and infra['plan__provider'] != Plan.CLOUDSTACK:
			LOG.info('Plan %s in environment %s with %s%% occupied' % (
				infra['plan__name'], infra['environment__name'], percent))
			LOG.info("Sending database infra notification...")
			context = {}
			context['plan'] = infra['plan__name']
			context['environment'] = infra['environment__name']
			context['used'] = used['used']
			context['capacity'] = infra['capacity']
			context['percent'] = percent
			email_notifications.databaseinfra_ending(context=context)

		task_history.update_status_for(TaskHistory.STATUS_SUCCESS,
		                               details='Databaseinfra Notification successfully sent to dbaas admins!')
	return


def database_notification_for_team(team=None):
	"""
    Notifies teams of database usage.
    if threshold_database_notification <= 0, the notification is disabled.
    """
	from logical.models import Database

	LOG.info("sending database notification for team %s" % team)
	threshold_database_notification = Configuration.get_by_name_as_int("threshold_database_notification", default=0)
	# if threshold_database_notification
	if threshold_database_notification <= 0:
		LOG.warning("database notification is disabled")
		return

	databases = Database.objects.filter(team=team)
	msgs = []
	for database in databases:
		used = database.used_size_in_mb
		capacity = database.total_size_in_mb
		try:
			percent_usage = (used / capacity) * 100
		except ZeroDivisionError:
			#database has no total size
			percent_usage = 0.0
		msg = "database %s => usage: %.2f | threshold: %.2f" % (
			database, percent_usage, threshold_database_notification)
		LOG.info(msg)
		msgs.append(msg)

		if not team.email:
			msgs.append("team %s has no email set and therefore no database usage notification will been sent" % team)
		else:
			if percent_usage >= threshold_database_notification:
				LOG.info("Sending database notification...")
				context = {}
				context['database'] = database.name
				context['team'] = team
				context['measure_unity'] = "MB"
				context['used'] = used
				context['capacity'] = capacity
				context['percent'] = "%.2f" % percent_usage
				context['environment'] = database.environment.name
				email_notifications.database_usage(context=context)

	return msgs


@app.task(bind=True)
@only_one(key="db_notification_key", timeout=20)
def database_notification(self):
	"""
    Create tasks for database notification by team
    if threshold_database_notification <= 0, the notification is disabled.
    """
	# get all teams and for each one create a new task
	LOG.info("retrieving all teams and sendind database notification")
	teams = Team.objects.all()
	msgs = {}

	for team in teams:
		###############################################
		# create task
		###############################################

		msgs[team] = database_notification_for_team(team=team)
		###############################################

	try:
		LOG.info("Messages: ")
		LOG.info(msgs)

		task_history = TaskHistory.register(request=self.request, user=None)
		task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details="\n".join(
			str(key) + ': ' + ', '.join(value) for key, value in msgs.items()))
	except Exception, e:
		task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

	return
