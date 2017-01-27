from __future__ import absolute_import
from dbaas.celery import app
from .models import TaskHistory


def check_tasks(task_history, celery_hosts):
    tasks = TaskHistory.objects.filter(
        task_status=TaskHistory.STATUS_RUNNING
    ).exclude(
        id=task_history.id
    )
    task_history.add_detail("\nTasks with status running: {}\n".format(len(tasks)))

    celery_tasks = get_celery_active_tasks(task_history, celery_hosts)
    task_history.add_detail("Celery running: {}\n".format(len(celery_tasks)))

    task_history.add_detail("Checking tasks status")

    tasks_with_problem = []
    for task in tasks:
        task_history.add_detail(
            "{} - {}".format(task.task_id, task.task_name), level=1
        )

        task = TaskHistory.objects.get(id=task.id)
        if task.is_running and task.task_id in celery_tasks:
            task_history.add_detail("OK: Running in celery", level=2)
            continue

        tasks_with_problem.append(task)
        task_history.add_detail("ERROR: Not running in celery", level=2)
        task_history.add_detail("Setting task to ERROR status", level=3)
        task.update_status_for(
            status=TaskHistory.STATUS_ERROR,
            details="Celery is not running this task"
        )

        database_upgrade = task.database_upgrades.first()
        if database_upgrade:
            task_history.add_detail(
                "Setting database upgrade {} status to ERROR".format(
                    database_upgrade.id
                ),
                level=3
            )
            database_upgrade.set_error()

    return tasks_with_problem


def get_celery_active_tasks(task_history, celery_hosts):
    task_history.add_detail('Collecting celery tasks...')
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
        task_history.add_detail('Host {} tasks:'.format(host), level=1)
        for task in tasks:
            task_id = task['id']
            if task_id == task_history.task_id:
                continue

            task_history.add_detail('{}'.format(task_id), level=2)
            active_tasks.append(task_id)

    return active_tasks
