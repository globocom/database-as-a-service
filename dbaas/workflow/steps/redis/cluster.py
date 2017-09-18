# -*- coding: utf-8 -*-
from workflow.steps.util.plan import PlanStep
from workflow.steps.util.base import BaseInstanceStep


class BaseClusterStep(PlanStep):

    @property
    def masters(self):
        return 3

    @property
    def cluster_command(self):
        return 'redis-trib.rb'

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

        assert '[OK] All nodes agree about slots configuration.' in str(output['stdout'])
        assert '[OK] All 16384 slots covered.' in str(output['stdout'])

        output = self.run_script(self.cluster_info_command)
        assert '[OK] 0 keys in {} masters.'.format(self.masters) in str(output['stdout'])
