from datetime import date, timedelta

from maintenance.models import TaskSchedule
from logical.models import Database


def register_schedule_task_restart_database(hostnames):
    today = date.today()
    try:
        databases = Database.objects.filter(
            databaseinfra__instances__hostname__hostname__in=hostnames
        ).distinct()
        for database in databases:
            print("Checking database {}".format(database.name))
            scheudled_tasks = TaskSchedule.objects.filter(
                status=TaskSchedule.SCHEDULED,
                database=database,
                method_path='restart_database'
            )
            if scheudled_tasks:
                print("Already scheduled for database {}!".format(
                    database.name)
                )
            else:
                task = TaskSchedule.objects.create(
                    method_path='restart_database',
                    scheduled_for=TaskSchedule.next_maintenance_window(
                        today + timedelta(days=2),
                        database.databaseinfra.maintenance_window,
                        database.databaseinfra.maintenance_day
                    ),
                    database=database
                )
                task.send_mail(is_new=True)
        print("Done")
    except Exception as err:
        print("Error: {}".format(err))
