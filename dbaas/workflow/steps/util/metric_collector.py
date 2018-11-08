from base import BaseInstanceStep
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from util import build_context_script
from util import exec_remote_command_host
import logging

LOG = logging.getLogger(__name__)

class MetricsCollector(BaseInstanceStep):

    def __init__(self, instance):
        super(MetricsCollector, self).__init__(instance)
        self.credential = get_credentials_for(
            self.environment, CredentialType.TELEGRAF)
        self.collector_allowed = self.credential.get_parameter_by_name(
            'collector_allowed')
        self.kafka_topic = self.credential.get_parameter_by_name(
            'kafka_topic')
        self.driver = self.infra.get_driver()

    @property
    def is_valid(self):
        return str(self.collector_allowed).lower() == 'true'

    @property
    def script_variables(self):
        user = self.driver.get_metric_collector_user(self.credential.user)
        password = self.driver.get_metric_collector_password(
            self.credential.password)
        create_telegraf_config = True
        if self.instance.instance_type == self.instance.REDIS_SENTINEL:
            if len(self.host.instances.all()) > 1:
                create_telegraf_config = False
        create_default_file = self.instance.instance_type in (
            self.instance.MYSQL, self.instance.MONGODB, self.instance.REDIS)
        variables = {
            'HOSTNAME': self.host.hostname.split('.')[0],
            'HOSTADDRESS': self.instance.address,
            'PORT': self.instance.port,
            'USER': user,
            'PASSWORD': password,
            'MYSQL': self.instance.instance_type == self.instance.MYSQL,
            'MONGODB': self.instance.instance_type == self.instance.MONGODB,
            'REDIS': self.instance.instance_type == self.instance.REDIS,
            'CREATE_TELEGRAF_CONFIG': create_telegraf_config,
            'CREATE_DEFAULT_FILE': create_default_file,
            'KAFKA_ENDPOINT': self.credential.endpoint,
            'KAFKA_TOPIC': self.kafka_topic,
        }
        return variables

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def exec_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(str(output))
        LOG.info("output: {}".format(output))
        return output


class ConfigureTelegraf(MetricsCollector):
    def __unicode__(self):
        return "Configuring Telegraf..."

    def do(self):
        if not self.is_valid: return
        template_script = self.plan.script.metric_collector_template
        script = build_context_script(self.script_variables, template_script)
        return self.exec_script(script)


class InstallTelegraf(MetricsCollector):
    def __unicode__(self):
        return "Installing Telegraf..."

    def do(self):
        if not self.is_valid: return
        script = "yum install telegraf -y"
        self.exec_script(script)


class RestartTelegraf(MetricsCollector):
    def __unicode__(self):
        return "Restarting Telegraf..."

    def do(self):
        if not self.is_valid: return
        script = "/etc/init.d/telegraf restart"
        self.exec_script(script)


class StopTelegraf(MetricsCollector):
    def __unicode__(self):
        return "Stopping Telegraf..."

    def do(self):
        if not self.is_valid: return
        script = "/etc/init.d/telegraf stop"
        self.exec_script(script)


class CreateMetricCollectorDatabaseUser(MetricsCollector):
    def __unicode__(self):
        return "Creating metric collector database user..."

    def do(self):
        if not self.is_valid: return
        if self.driver.check_instance_is_master(self.instance):
            self.driver.create_metric_collector_user(
                username=self.credential.user,
                password=self.credential.password)

    def undo(self):
        if not self.is_valid: return
        if self.driver.check_instance_is_master(self.instance):
            self.driver.remove_metric_collector_user(
                username=self.credential.user)
