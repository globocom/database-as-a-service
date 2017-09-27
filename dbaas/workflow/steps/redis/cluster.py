# -*- coding: utf-8 -*-
from system.models import Configuration
from workflow.steps.util.plan import PlanStep


class BaseClusterStep(PlanStep):

    @property
    def masters(self):
        return len(self.infra.get_driver().get_master_instance())

    @property
    def cluster_command(self):
        return Configuration.get_by_name('redis_trib_path')

    @property
    def cluster_create_command(self):
        return 'yes yes | {{ CLUSTER_COMMAND }} create --password {{ PASSWORD }} --replicas {{ CLUSTER_REPLICAS }} {% for address in CLUSTER_ADDRESSES %} {{ address }} {% endfor %}'

    @property
    def cluster_check_command(self):
        return '{{ CLUSTER_COMMAND }} check --password {{ PASSWORD }} {{ CLUSTER_ADDRESS }}'

    @property
    def cluster_info_command(self):
        return '{{ CLUSTER_COMMAND }} info --password {{ PASSWORD }} {{ CLUSTER_ADDRESS }}'

    @property
    def node_config_file(self):
        return 'nodes.conf'

    @property
    def script_variables(self):
        variables = {
            'CLUSTER_COMMAND': self.cluster_command,
            'PASSWORD': self.infra.password
        }

        variables.update(self.get_variables_specifics())
        return variables


class CreateCluster(BaseClusterStep):

    def __unicode__(self):
        return "Configuring Redis Cluster..."

    @property
    def masters(self):
        return len(self.infra.get_driver().get_master_instance())/2

    def get_variables_specifics(self):
        instances = self.infra.instances.all()
        return {
            'CLUSTER_REPLICAS': (len(instances)-self.masters)/self.masters,
            'CLUSTER_ADDRESSES': [
                '{}:{}'.format(instance.hostname.address, instance.port)
                for instance in instances
            ]
        }

    def do(self):
        if self.instance.id != self.infra.instances.first().id:
            return

        self.run_script(self.cluster_create_command)


class CheckClusterStatus(BaseClusterStep):

    def __unicode__(self):
        return "Checking cluster status..."

    def get_variables_specifics(self):
        return {
            'CLUSTER_ADDRESS': '{}:{}'.format(
                self.instance.hostname.address, self.instance.port
            )
        }

    def do(self):
        output = self.run_script(self.cluster_check_command)
        self.check_response(
            '[OK] All nodes agree about slots configuration.', output['stdout']
        )
        self.check_response('[OK] All 16384 slots covered.', output['stdout'])

        output = self.run_script(self.cluster_info_command)
        self.check_response(
            '[OK] 0 keys in {} masters.'.format(self.masters), output['stdout']
        )

    def check_response(self, expected, response):
        response = str(response)
        if expected in response:
            return True

        raise AssertionError('"{}" not in {}'.format(expected, response))


class SaveNodeConfig(BaseClusterStep):

    def __unicode__(self):
        return "Saving node config..."

    def do(self):
        self.run_script('cp /data/{} /tmp/'.format(self.node_config_file))


class RestoreNodeConfig(BaseClusterStep):

    def __unicode__(self):
        return "Restoring node config..."

    def do(self):
        self.run_script('cp /tmp/{} /data/'.format(self.node_config_file))
