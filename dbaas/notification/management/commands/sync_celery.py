# -*- coding: utf-8 -*-
from __future__ import absolute_import
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from dbaas.celery import app
from util import full_stack
from notification.models import TaskHistory


class Command(BaseCommand):
    help = "Check if all Tasks with status running are in celery"

    option_list = BaseCommand.option_list + (
        make_option(
            "-n",
            "--celery_hosts",
            dest = "celery_hosts",
            help = "Number of celery hosts",
            type="int",
        ),
    )
    
    def __init__(self):
        super(Command, self).__init__()

        self.task = TaskHistory()
        self.task.task_id = "crontab"
        self.task.task_name = "sync_celery_tasks"
        self.task.task_status = TaskHistory.STATUS_RUNNING
        self.task.save()
        self.task.add_detail('Syncing metadata tasks with celery tasks')

    def handle(self, *args, **kwargs):
        if not kwargs['celery_hosts']:
            raise CommandError("Please specified the --celery_hosts count")

        try:
            tasks_with_problem = self.check_tasks(kwargs['celery_hosts'])
        except Exception as e:
            self.task.update_status_for(
                TaskHistory.STATUS_ERROR,
                'Could not check celery tasks.\n{}{}'.format(full_stack(), e)
            )
            return

        problems = len(tasks_with_problem)
        status = TaskHistory.STATUS_SUCCESS
        if problems > 0:
            status = TaskHistory.STATUS_WARNING
        self.task.update_status_for(status, 'Problems: {}'.format(problems))

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
            if task.is_running and task.task_id in celery_tasks:
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

        return tasks_with_problem

    def get_celery_active_tasks(self, celery_hosts):
        self.task.add_detail('Collecting celery tasks...')
        actives = app.control.inspect().active()

        activated_hosts = actives.keys()
        if len(activated_hosts) != celery_hosts:
            raise EnvironmentError(
                "I'm expecting {} celery hosts and found {}! {}".format(
                    celery_hosts, len(activated_hosts), activated_hosts
                )
            )

        active_tasks = []
        for host, tasks in actives.items():
            self.task.add_detail('Host {} tasks:'.format(host), level=1)
            for task in tasks:
                task_id = task['id']

                self.task.add_detail('{}'.format(task_id), level=2)
                active_tasks.append(task_id)

        return active_tasks
