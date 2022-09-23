from notification.models import TaskHistory


class TaskRegisterBase:
    TASK_CLASS = TaskHistory

    @classmethod
    def create_task(cls, params):
        database = params.pop('database', None)

        task = cls.TASK_CLASS()

        if database:
            task.object_id = database.id
            task.object_class = database._meta.db_table
            database_name = database.name
        else:
            database_name = params.pop('database_name', '')

        task.database_name = database_name

        for k, v in params.iteritems():
            setattr(task, k, v)

        task.save()

        return task