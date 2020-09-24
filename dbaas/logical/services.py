from . import exceptions
from maintenance import models
from logical.validators import (
    check_is_database_enabled,
    check_is_database_dead
)
from logical.errors import DisabledDatabase
from system.models import Configuration
from notification.tasks import TaskRegister


class AddReadOnlyInstanceService:

    def __init__(self, request, database, retry=False, rollback=False):
        self.request = request
        self.database = database
        self.manager = None
        self.number_of_instances = 0
        self.number_of_instances_before = 0
        self.retry = retry
        self._rollback = rollback
        self.task_params = {}

        self.initialize()

    def initialize(self):
        self.load_manager()

    def load_manager(self):
        if self.retry or self._rollback:
            self.manager = models.AddInstancesToDatabase.objects.filter(
                database=self.database
            ).last()
            self.number_of_instances = self.manager.number_of_instances

            if not self.manager:
                error = "Database does not have add_database_instances"
                raise exceptions.ManagerNotFound(error)
            elif not self.manager.is_status_error:
                error = ("Cannot do retry/rollback last add_instances_to_database. "
                         "Status is '{}'!").format(
                            self.manager.get_status_display())
                raise exceptions.ManagerInvalidStatus(error)

    def load_number_of_instances(self):
        if self.retry or self._rollback:
            self.number_of_instances = self.manager.number_of_instances
            self.number_of_instances_before = (
                self.manager.number_of_instances_before
            )
        else:
            if 'add_read_qtd' in self.request.POST:
                self.number_of_instances = int(
                    self.request.POST['add_read_qtd']
                )
            self.number_of_instances_before = (
                self.database.infra.last_vm_created
            )

    def check_database_status(self):
        try:
            if not self.retry:
                check_is_database_dead(self.database.id, 'Add read-only instances')
            check_is_database_enabled(
                self.database.id,
                'Add read-only instances',
                ['notification.tasks.add_instances_to_database',
                 'notification.tasks.add_instances_to_database_rollback']
            )
            return (True, '')
        except DisabledDatabase as err:
            return (False, err.message)

    def is_ha(self):
        if not self.database.plan.replication_topology.has_horizontal_scalability:
            return False
        return True

    def execute(self):
        self.load_number_of_instances()

        if not self.number_of_instances:
            raise exceptions.RequiredNumberOfInstances(
                'Number of instances is required'
            )

        status, message = self.check_database_status()
        if not status:
            raise exceptions.DatabaseNotAvailable(message)

        if not self.is_ha():
            raise exceptions.DatabaseIsNotHA(
                'Database topology do not have horizontal scalability'
            )

        max_read_hosts = Configuration.get_by_name_as_int('max_read_hosts', 5)
        qtd_new_hosts = self.number_of_instances
        current_read_nodes = len(self.database.infra.instances.filter(read_only=True))
        total_read_hosts = qtd_new_hosts + current_read_nodes
        if total_read_hosts > max_read_hosts:
            raise exceptions.ReadOnlyHostsLimit(
                ('Current limit of read only hosts is {} and you are trying '
                 'to setup {}').format(
                    max_read_hosts, total_read_hosts
                )
            )

        self.task_params = dict(
            database=self.database,
            user=self.request.user,
            number_of_instances=qtd_new_hosts,
            number_of_instances_before_task=self.number_of_instances_before
        )

        if self.retry:
            since_step = self.manager.current_step
            self.task_params['since_step'] = since_step

        TaskRegister.database_add_instances(**self.task_params)

    def rollback(self):
        self.load_number_of_instances()

        if not self.number_of_instances:
            raise exceptions.RequiredNumberOfInstances(
                'Number of instances is required'
            )

        status, message = self.check_database_status()
        if not status:
            raise exceptions.DatabaseNotAvailable(message)

        if not self.is_ha():
            raise exceptions.DatabaseIsNotHA(
                'Database topology do not have horizontal scalability'
            )

        TaskRegister.database_add_instances_rollback(
            self.manager, self.request.user
        )


class UpgradeDatabaseService:

    def __init__(self, request, database, retry=False, rollback=False):
        self.request = request
        self.database = database
        self.manager = None
        self.retry = retry
        self._rollback = rollback
        self.task_params = {}

        self.initialize()

    def initialize(self):
        self.load_manager()

    def load_manager(self):
        if self.retry or self._rollback:
            self.manager = models.DatabaseUpgrade.objects.filter(
                database=self.database
            ).last()

            if not self.manager:
                error = "Database does not have upgrade_database"
                raise exceptions.ManagerNotFound(error)
            elif not self.manager.is_status_error:
                error = ("Cannot do retry/rollback last upgrade_database. "
                         "Status is '{}'!").format(
                            self.manager.get_status_display())
                raise exceptions.ManagerInvalidStatus(error)

    def check_database_status(self):
        try:
            if not self.retry:
                check_is_database_dead(self.database.id, 'Upgrade Database')
            check_is_database_enabled(
                self.database.id,
                'Upgrade Database',
                ['notification.tasks.upgrade_database']
            )
            return (True, '')
        except DisabledDatabase as err:
            return (False, err.message)

    def execute(self):
        status, message = self.check_database_status()
        if not status:
            raise exceptions.DatabaseNotAvailable(message)

        self.task_params = dict(
            database=self.database,
            user=self.request.user
        )

        if not self.database.infra.plan.engine_equivalent_plan:
            raise exceptions.DatabaseUpgradePlanNotFound(
                "Source plan do not has equivalent plan to upgrade."
            )

        if self.retry:
            since_step = self.manager.current_step
            self.task_params['since_step'] = since_step

        TaskRegister.database_upgrade(**self.task_params)

    def rollback(self):
        pass


class RemoveReadOnlyInstanceService:

    def __init__(self, request, database, instance=None, retry=False, rollback=False):
        self.request = request
        self.database = database
        self.manager = None
        self.retry = retry
        self._rollback = rollback
        self.task_params = {}
        self.instance = instance

        self.initialize()

    def initialize(self):
        self.load_manager()

    def load_manager(self):
        if self.retry or self._rollback:
            self.manager = models.RemoveInstanceDatabase.objects.filter(
                database=self.database
            ).last()

            if not self.manager:
                error = "Database does not have upgrade_database"
                raise exceptions.ManagerNotFound(error)
            elif not self.manager.is_status_error:
                error = ("Cannot do retry/rollback last upgrade_database. "
                         "Status is '{}'!").format(
                            self.manager.get_status_display())
                raise exceptions.ManagerInvalidStatus(error)

            self.instance = self.manager.instance

    def check_database_status(self):
        try:
            check_is_database_dead(self.database.id, 'Remove read-only instances')
            check_is_database_enabled(
                self.database.id,
                'Remove read-only instances',
                ['notification.tasks.remove_readonly_instance']
            )
            return (True, '')
        except DisabledDatabase as err:
            return (False, err.message)

    def execute(self):
        status, message = self.check_database_status()
        if not status:
            raise exceptions.DatabaseNotAvailable(message)

        if not self.instance.read_only:
            raise exceptions.HostIsNotReadOnly(
                "Host is not read only, cannot be removed."
            )

        self.task_params = dict(
            database=self.database,
            user=self.request.user,
            instance=self.instance
        )

        if self.retry:
            since_step = self.manager.current_step
            self.task_params['since_step'] = since_step
            self.task_params['step_manager'] = self.manager

        TaskRegister.database_remove_instance(**self.task_params)

    def rollback(self):
        pass


class DatabaseMigrateEngineService:

    def __init__(
        self, request, database, target_plan=None, retry=False, rollback=False
    ):
        self.request = request
        self.database = database
        self.manager = None
        self.retry = retry
        self._rollback = rollback
        self.task_params = {}
        self.target_plan = target_plan

        self.initialize()

    def initialize(self):
        self.load_manager()

    def load_manager(self):
        if self.retry or self._rollback:
            self.manager = models.DatabaseMigrateEngine.objects.filter(
                database=self.database
            ).last()

            if not self.manager:
                error = "Database does not have migrate_engine"
                raise exceptions.ManagerNotFound(error)
            elif not self.manager.is_status_error:
                error = ("Cannot do retry/rollback last migrate_engine. "
                         "Status is '{}'!").format(
                            self.manager.get_status_display())
                raise exceptions.ManagerInvalidStatus(error)
            self.target_plan = self.manager.target_plan

    def check_database_status(self):
        try:
            if not self.retry:
                check_is_database_dead(
                    self.database.id, 'Database Migrate Engine'
                )
            check_is_database_enabled(
                self.database.id,
                'Database Migrate Engine',
                ['notification.tasks.migrate_engine']
            )
            return (True, '')
        except DisabledDatabase as err:
            return (False, err.message)

    def execute(self):
        status, message = self.check_database_status()
        if not status:
            raise exceptions.DatabaseNotAvailable(message)

        self.task_params = dict(
            database=self.database,
            target_plan=self.target_plan,
            user=self.request.user
        )

        if self.retry:
            self.task_params['since_step'] = self.manager.current_step

        TaskRegister.engine_migrate(**self.task_params)

    def rollback(self):
        pass
