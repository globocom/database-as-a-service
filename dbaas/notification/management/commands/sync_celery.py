# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
from optparse import make_option
import socket
from django.core.management.base import BaseCommand, CommandError
from dbaas.celery import app
from util import full_stack
from notification.models import TaskHistory
from django_redis import get_redis_connection
from django.conf import settings
from redis import Redis


class CeleryActivesNodeError(EnvironmentError):

    def __init__(self, expected, current_actives):
        msg = "I'm expecting {} celery hosts and found {}! {}".format(
            expected, len(current_actives), current_actives
        )
        super(EnvironmentError, self).__init__(msg)


class Command(BaseCommand):
    help = "Check if all Tasks with status running are in celery"

    option_list = BaseCommand.option_list + (
        make_option(
            "-n",
            "--celery_hosts",
            dest="celery_hosts",
            help="Number of celery hosts",
            type="int",
        ),
    )

    def __init__(self):
        super(Command, self).__init__()

        self.task = TaskHistory()
        self.task.task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.task.task_name = "sync_celery_tasks"
        self.task.relevance = TaskHistory.RELEVANCE_WARNING
        self.task.task_status = TaskHistory.STATUS_RUNNING
        self.task.context = {'hostname': socket.gethostname()}
        self.task.save()
        self.task.add_detail('Syncing metadata tasks with celery tasks')
        self.unique_tasks = [{
            'name': 'backup.tasks.make_databases_backup',
            'unique_key': 'makedatabasebackupkey'
        }]
        self._redis_conn = None


    @property
    def redis_conn(self):
        if not self._redis_conn:
            self._redis_conn = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD
            )
        return self._redis_conn

    def handle(self, *args, **kwargs):
        self.task.arguments = {'args': args, 'kwargs': kwargs}
        if not kwargs['celery_hosts']:
            raise CommandError("Please specified the --celery_hosts count")

        try:
            tasks_with_problem = self.check_tasks(kwargs['celery_hosts'])
        except CeleryActivesNodeError as celery_error:
            self.task.update_status_for(
                TaskHistory.STATUS_WARNING,
                'Could not check celery tasks.\n{}{}'.format(
                    full_stack(), celery_error
                )
            )
            return
        except Exception as e:
            self.task.update_status_for(
                TaskHistory.STATUS_ERROR,
                'Could not execute task.\n{}{}'.format(full_stack(), e)
            )
            return

        problems = len(tasks_with_problem)
        status = TaskHistory.STATUS_SUCCESS
        if problems > 0:
            status = TaskHistory.STATUS_WARNING
        self.task.update_status_for(status, 'Problems: {}'.format(problems))

        self.check_unique_keys()

    def check_unique_keys(self):
        for unique_task in self.unique_tasks:
            task_running = TaskHistory.objects.filter(
                task_status='RUNNING',
                task_name=unique_task['name']
            )
            if not task_running:
                unique_key = unique_task['unique_key']
                if unique_key in self.redis_conn.keys():
                    self.redis_conn.delete(unique_key)

    def check_tasks(self, celery_hosts):
        tasks_running = TaskHistory.objects.filter(
            task_status=TaskHistory.STATUS_RUNNING
        ).exclude(
            id=self.task.id
        )
        self.task.add_detail(
            "\nTasks with status running: {}\n".format(len(tasks_running))
        )

        celery_tasks = self.get_celery_active_tasks(celery_hosts)
        self.task.add_detail("Celery running: {}\n".format(len(celery_tasks)))

        tasks_with_problem = []
        self.task.add_detail("Checking tasks status")
        for task in tasks_running:
            self.task.add_detail(
                "{} - {}".format(task.task_id, task.task_name), level=1
            )

            task = TaskHistory.objects.get(id=task.id)
            if not task.is_running:
                self.task.add_detail(
                    "OK: Tasks was finished with {}".format(task.task_status),
                    level=2
                )
                continue

            if task.task_id in celery_tasks:
                self.task.add_detail("OK: Running in celery", level=2)
                continue

            tasks_with_problem.append(task)
            self.task.add_detail("ERROR: Not running in celery", level=2)
            self.task.add_detail("Setting task to ERROR status", level=3)

            task.update_status_for(
                status=TaskHistory.STATUS_ERROR,
                details="Celery is not running this task"
            )

            database_upgrade = task.database_upgrades.first()
            if database_upgrade:
                self.task.add_detail(
                    "Setting database upgrade {} status to ERROR".format(
                        database_upgrade.id
                    ), level=3
                )
                database_upgrade.set_error()

            database_resize = task.database_resizes.first()
            if database_resize:
                self.task.add_detail(
                    "Setting database resize {} status to ERROR".format(
                        database_resize.id
                    ), level=3
                )
                database_resize.set_error()

            database_create = task.create_database.first()
            if database_create:
                self.task.add_detail(
                    "Setting database create {} status to ERROR".format(
                        database_create.id
                    ), level=3
                )
                database_create.set_error()

            database_restore = task.database_restore.first()
            if database_restore:
                self.task.add_detail(
                    "Setting database restore {} status to ERROR".format(
                        database_restore.id
                    ), level=3
                )
                database_restore.set_error()

        return tasks_with_problem

    def get_celery_active_tasks(self, expected_hosts):
        self.task.add_detail('Collecting celery tasks...')
        actives = app.control.inspect().active()

        activated_hosts = []
        if actives:
            activated_hosts = actives.keys()

        if len(activated_hosts) != expected_hosts:
            raise CeleryActivesNodeError(expected_hosts, activated_hosts)

        active_tasks = []
        for host, tasks in actives.items():
            self.task.add_detail('Host {} tasks:'.format(host), level=1)
            for task in tasks:
                task_id = task['id']

                self.task.add_detail('{}'.format(task_id), level=2)
                active_tasks.append(task_id)

        return active_tasks
