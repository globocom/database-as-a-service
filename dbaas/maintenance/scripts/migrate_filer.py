from datetime import datetime
from socket import gethostname
from notification.models import TaskHistory
from logical.models import Database
from util.providers import get_filer_migrate_steps
from workflow.workflow import steps_for_instances
from dbaas.celery import app
from util import email_notifications, get_worker_name


class FilerMigrate(object):

    def __init__(self, databases=None):
        self._task = None
        self._databases = databases or None

    @property
    def databases(self):
        if not self._databases:
            self._databases = Database.objects.all()
        return self._databases

    @databases.setter
    def databases(self, val):
        self._databases = val

    @property
    def task(self):
        if not self._task:
            self._task = self.register_task()
        return self._task

    def do(self):
        if not self.databases:
            self.load_all_databases()
        self.start_migration()

    def load_all_databases(self):
        self.task.add_detail("Getting all databases...")
        self.databases = Database.objects.all()
        self.task.add_detail("Loaded\n", level=2)

    def migrate_filer_disk_for_database(self, database):
        infra = database.infra
        task_history = TaskHistory()
        task_history.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_history.task_name = "migrate_filer_disk_for_database"
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        task_history.task_status = TaskHistory.STATUS_WAITING
        task_history.context = {'hostname': gethostname()}
        task_history.user = 'admin'
        task_history.db_id = database.id
        task_history.database_name = database.name
        task_history.arguments = 'Database_name: {}'.format(database.name)
        task_history.save()
        task = task_history
        if database.is_being_used_elsewhere():
            task.add_detail(
                "ERROR-{}-Being used to another task".format(database.name),
                level=2
            )
            task.set_status_error(
                'Database is being used by another task'
            )
            return
        task.add_detail(
            "Migrating disk for database {}...".format(database.name),
            level=2
        )
        class_path = infra.plan.replication_topology.class_path
        steps = get_filer_migrate_steps(class_path)
        if not steps_for_instances(steps, self._get_instances(infra), task):
            task.set_status_error('Could not migrate filer')
            return
        task.set_status_success('Migrate filer finished with success')

    def start_migration(self):
        for database in self.databases:
            self.migrate_filer_disk_for_database(database)

    def _get_instances(self, infra):
        return [
            host.database_instance() or host.non_database_instance()
            for host in infra.hosts
        ]

    def register_task(self, database):
        task_history = TaskHistory()
        task_history.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_history.task_name = "migrate_filer_disk_for_database"
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        task_history.task_status = TaskHistory.STATUS_WAITING
        task_history.context = {'hostname': gethostname()}
        task_history.user = 'admin'
        task_history.db_id = database.id
        task_history.database_name = database.name
        task_history.arguments = 'Database_name: {}'.format(database.name)
        task_history.save()
        return task_history
