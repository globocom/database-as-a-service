# -*- coding: utf-8 -*-
from workflow.steps.util.plan import PlanStep


class CreateCluster(PlanStep):

    def __unicode__(self):
        return "Configuring Redis Cluster..."

    def get_variables_specifics(self):
        instances = self.infra.instances.all()
        return {
            'CLUSTER_REPLICAS': len(instances)/6,
            'CLUSTER_ADDRESSES': [
                '{}:{}'.format(instance.hostname.address, instance.port)
                for instance in instances
            ]
        }

    def do(self):
        if self.instance.id != self.infra.instances.first().id:
            return

        self.run_script(self.plan.script.start_replication_template)


class CheckIsUp(PlanStep)


        'check'
        '[OK] All nodes agree about slots configuration.'
        '[OK] All 16384 slots covered.'


        'info'
        '[OK] 0 keys in 3 masters.'
