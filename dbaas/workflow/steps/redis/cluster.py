# -*- coding: utf-8 -*-
from system.models import Configuration
from workflow.steps.util.plan import PlanStep
from time import sleep


class BaseClusterStep(PlanStep):

    def __init__(self, instance):
        super(BaseClusterStep, self).__init__(instance)
        self.driver = self.infra.get_driver()

    @property
    def master(self):
        return self.driver.get_master_for(self.instance).hostname

    @property
    def masters(self):
        return len(self.driver.get_master_instance())

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
    def cluster_slave_node_command(self):
        return '{{ CLUSTER_COMMAND }} add-node --password {{ PASSWORD }} --slave --master-id {{ MASTER_ID }} {{ NEW_NODE_ADDRESS }} {{ CLUSTER_ADDRESS }}'

    @property
    def cluster_del_node_command(self):
        commands = [
            '{{ CLUSTER_COMMAND }} del-node --password {{ PASSWORD }} {{ CLUSTER_ADDRESS }} {{ NODE_ID }}',
            'rm -f /data/data/redis.aof',
            'rm -f /data/data/dump.rdb',
            'rm -f /data/{}'.format(self.node_config_file),
            '/etc/init.d/redis start'
        ]
        return ' && '.join(commands)

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

    def check_response(self, expected, response):
        response = str(response)
        if expected in response:
            return True

        raise AssertionError('"{}" not in {}'.format(expected, response))


class CreateCluster(BaseClusterStep):

    def __unicode__(self):
        return "Configuring Redis Cluster..."

    @property
    def masters(self):
        return len(self.driver.get_master_instance())/2

    def get_variables_specifics(self):
        instances = self.infra.instances.all()
        instances_even = []
        instances_odd = []
        for i in range(len(instances)):
            if i % 2 == 0:
                instances_even.append(instances[i])
            else:
                instances_odd.append(instances[i])
        instances = instances_even + instances_odd
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
                self.host.address, self.instance.port
            )
        }

    def do(self):
        output = self.run_script(self.cluster_check_command)
        self.check_response(
            '[OK] All nodes agree about slots configuration.', output['stdout']
        )
        self.check_response('[OK] All 16384 slots covered.', output['stdout'])


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


class SetInstanceShardTag(BaseClusterStep):

    def __unicode__(self):
        return "Setting instance shard tag..."

    def __init__(self, instance):
        super(SetInstanceShardTag, self).__init__(instance)
        self.instances = self.infra.instances.all()

    def check_cluster_status(self):
        for cluster_node in self.cluster_nodes:
            if cluster_node['link-state'] != 'connected':
                msg = "The node {}:{} is not connected to the cluster.".format(
                    cluster_node['host'], cluster_node['port']
                )
                raise AssertionError(msg)

    def identify_cluster_nodes_masters(self):
        attempt = 1
        retries = 10
        interval = 10
        while True:
            shard = 1
            for instance in self.instances:
                for cluster_node in self.cluster_nodes:
                    if cluster_node['host'] == instance.address and cluster_node['port'] == instance.port:
                        if cluster_node['master'] is None:
                            cluster_node['shard'] = "{0:02d}".format(shard)
                            shard += 1
            masters = shard - 1
            if len(self.instances) / 2 == masters:
                break
            attempt += 1
            if attempt == retries - 1:
                msg = "Could not get cluster configuration. There are {} masters and {} instances".format(masters, len(self.instances))
                raise Exception(msg)
            sleep(interval)
            self.retrieve_cluster_nodes_info()

    def update_instance_shard(self):
        for cluster_node in self.cluster_nodes:
            if cluster_node['master']:
                for cluster_node_master in self.cluster_nodes:
                    if cluster_node_master['id'] == cluster_node['master']:
                        cluster_node['shard'] = cluster_node_master['shard']

        for instance in self.instances:
            for cluster_node in self.cluster_nodes:
                if cluster_node['host'] == instance.address and cluster_node['port'] == instance.port:
                    instance.shard = cluster_node['shard']
                    instance.save()

    def retrieve_cluster_nodes_info(self):
        cluster_client = self.driver.get_cluster_client(None)
        self.cluster_nodes = cluster_client.cluster_nodes()

    def do(self):
        if self.instance.id != self.instances.first().id:
            return

        self.retrieve_cluster_nodes_info()
        self.check_cluster_status()
        self.identify_cluster_nodes_masters()
        self.update_instance_shard()


class AddSlaveNode(BaseClusterStep):

    def __unicode__(self):
        return "Add node..."

    def __init__(self, instance):
        super(AddSlaveNode, self).__init__(instance)
        self.new_host_address = self.host.address

    def get_variables_specifics(self):
        return {
            'MASTER_ID': self.driver.get_node_id(
                self.instance, self.master.address, self.instance.port
            ),
            'NEW_NODE_ADDRESS': '{}:{}'.format(
                self.new_host_address, self.instance.port
            ),
            'CLUSTER_ADDRESS': '{}:{}'.format(
                self.master.address, self.instance.port
            )
        }

    def do(self):
        output = self.run_script(self.cluster_slave_node_command)
        self.check_response(
            '[OK] New node added correctly.', output['stdout']
        )

    def undo(self):
        remove = RemoveNode(self.instance)
        remove.new_host_address = self.host.address
        remove.run_script_host = self.host
        remove.do()


class RemoveNode(BaseClusterStep):

    def __unicode__(self):
        return "Remove node..."

    def __init__(self, instance):
        super(RemoveNode, self).__init__(instance)
        self.remove_address = self.instance.address
        self.run_script_host = self.instance.hostname

    def get_variables_specifics(self):
        return {
            'CLUSTER_ADDRESS': '{}:{}'.format(
                self.master.address, self.instance.port
            ),
            'NODE_ID': self.driver.get_node_id(
                self.instance, self.remove_address, self.instance.port
            ),
        }

    def do(self):
        output = self.run_script(self.cluster_del_node_command)
        self.check_response(
            'SHUTDOWN the node', output['stdout']
        )

    def undo(self):
        instance = self.instance
        instance.address = self.host.address
        add = AddSlaveNode(instance)
        add.new_host_address = self.instance.hostname.address
        add.do()
