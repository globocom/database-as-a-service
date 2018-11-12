from datetime import datetime
from socket import gethostname
from notification.models import TaskHistory
from physical.models import DatabaseInfra, Instance
from util.providers import get_switch_write_instance_steps
from workflow.steps.util.host_provider import Provider, \
    HostProviderInfoException
from workflow.workflow import steps_for_instances


class SwitchMasters(object):

    def __init__(self, target_zone, instances=None):
        self.zone = target_zone
        self._task = None

        self.instances = []
        if instances:
            self.instances = instances

    @property
    def task(self):
        if not self._task:
            self._task = self.register_task()
        return self._task

    def do(self):
        if not self.instances:
            self.load_all_masters()
        self.start_switch()

    def load_all_masters(self):
        self.task.add_detail("Getting all masters...")
        for infra in DatabaseInfra.objects.all():
            if not infra.databases.exists():
                continue
            driver = infra.get_driver()
            infra_masters = driver.get_master_instance()
            if isinstance(infra_masters, Instance):
                infra_masters = [infra_masters]
            self.instances += infra_masters
        self.task.add_detail("Loaded\n", level=2)

    def start_switch(self):
        self.task.add_detail("Switching master in {}...".format(self.zone))
        for instance in self.instances:
            infra = instance.databaseinfra
            env = infra.environment
            host = instance.hostname
            hp = Provider(instance, env)
            try:
                info = hp.host_info(host)
            except HostProviderInfoException as e:
                self.task.add_detail("ERROR-{}-{}".format(host, e), level=2)
                self.task.set_status_error('Could not load host info')
                return

            if info["zone"] != self.zone:
                self.task.add_detail(
                    "OK-{}-{}".format(host, info["zone"]), level=2
                )
                continue

            database = infra.databases.first()
            if database.is_being_used_elsewhere():
                self.task.add_detail(
                    "ERROR-{}-Being used to another task".format(host),
                    level=2
                )
                self.task.set_status_error(
                    'Database is being used by another task'
                )
                return

            self.task.add_detail(
                "SWITCHING-{}-{}...".format(host, info["zone"]),
                level=2
            )
            class_path = infra.plan.replication_topology.class_path
            steps = get_switch_write_instance_steps(class_path)
            if not steps_for_instances(steps, [instance], self.task):
                self.task.set_status_error('Could not switch all masters')
                return
        self.task.set_status_success('Could switch all masters')

    def register_task(self):
        task_history = TaskHistory()
        task_history.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_history.task_name = "switch_masters_in_zone"
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        task_history.task_status = TaskHistory.STATUS_RUNNING
        task_history.context = {'hostname': gethostname()}
        task_history.user = 'admin'
        task_history.save()
        return task_history
