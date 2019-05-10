from datetime import datetime
from socket import gethostname
from notification.models import TaskHistory
from logical.models import Database
from util.providers import get_filer_migrate_steps
from workflow.workflow import steps_for_instances
from maintenance.models import FilerMigrate as FilerMigrateManager


class FilerMigrate(object):
    TASK_NAME = "migrate_filer_disk_for_database"

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

    def _can_run(self, database, task):
        if database.is_being_used_elsewhere([self.TASK_NAME]):
            task.add_detail(
                "ERROR-{}-Being used to another task".format(database.name),
                level=2
            )
            task.set_status_error(
                'Database is being used by another task'
            )
            return
        return True

    def set_error(self, task, step_manager):
        task.set_status_error('Could not migrate filer')
        step_manager.set_error()
        print('task {} with status {}.'.format(
            task.id,
            task.task_status)
        )

    def migrate_filer_disk_for_database(self, database):

        infra = database.infra
        class_path = infra.plan.replication_topology.class_path
        steps = get_filer_migrate_steps(class_path)
        task = self.register_task(database)
        instances = self._get_instances(infra)
        step_manager = self.register_step_manager(task, instances)
        if not self._can_run(database, task):
            self.set_error(task, step_manager)
            return
        task.add_detail(
            "Migrating disk for database {}...".format(database.name),
            level=2
        )
        steps_result = steps_for_instances(
            steps,
            instances,
            task,
            step_counter_method=step_manager.update_step,
            since_step=step_manager.current_step
        )
        if not steps_result:
            self.set_error(task, step_manager)
            return
        task.set_status_success('Migrate filer finished with success')

    def start_migration(self):
        for database in self.databases:
            self.migrate_filer_disk_for_database(database)

    def _get_instances(self, infra):
        instances = []
        for host in infra.hosts:
            database_instance = host.database_instance()
            if database_instance:
                instances.append(database_instance)
        return instances

    def register_step_manager(self, task, instances):
        old_step_manager = FilerMigrateManager.objects.filter(
            database_id=task.db_id,
            can_do_retry=True,
            status=FilerMigrateManager.ERROR
        )
        if old_step_manager.exists():
            step_manager = old_step_manager[0]
            step_manager.id = None
            step_manager.save()
        else:
            step_manager = FilerMigrateManager()
        step_manager.task = task
        original_export_id = ''
        for instance in instances:
            active_volume = instance.hostname.volumes.get(is_active=True)
            original_export_id += 'host_{}: export_{} '.format(
                active_volume.host.id,
                active_volume.identifier
            )
        step_manager.original_export_id = original_export_id
        step_manager.database_id = task.db_id
        step_manager.save()
        return step_manager

    def register_task(self, database):
        task_history = TaskHistory()
        task_history.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_history.task_name = self.TASK_NAME
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        task_history.task_status = TaskHistory.STATUS_RUNNING
        task_history.context = {'hostname': gethostname()}
        task_history.user = 'admin'
        task_history.db_id = database.id
        task_history.object_class = "logical_database"
        task_history.object_id = database.id
        task_history.database_name = database.name
        task_history.arguments = 'Database_name: {}'.format(database.name)
        task_history.save()
        return task_history
