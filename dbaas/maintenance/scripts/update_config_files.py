from datetime import datetime
from notification.models import TaskHistory
from workflow.workflow import steps_for_instances
from workflow.steps.util.plan import ConfigureOnlyDBConfigFile
from socket import gethostname

class UpdateConfigFiles(object):
    def __init__(self, infras):
        self.infras = infras
        self._task = None

    @property
    def task(self):
        if not self._task:
            self._task = self.register_task()
        return self._task

    def register_task(self):
        task_history = TaskHistory()
        task_history.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        task_history.task_name = "update_config_files"
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        task_history.task_status = TaskHistory.STATUS_RUNNING
        task_history.context = {'hostname': gethostname()}
        task_history.user = 'admin'
        task_history.save()
        return task_history

    def do(self):
        self.task.add_detail("Update Config Files")
        for infra in self.infras:
            for instance in infra.instances.all():
                self.task.add_detail(
                    "Updating config file for {}...".format(instance),
                    level=2
                )
                config = ConfigureOnlyDBConfigFile(instance)
                config.do()
        self.task.set_status_success('Files updated successfully.')