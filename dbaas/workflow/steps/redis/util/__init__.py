# -*- coding: utf-8 -*-
import logging
from util import build_context_script
from workflow.steps.util import test_bash_script_error

LOG = logging.getLogger(__name__)


def change_slave_priority_file(host, original_value, final_value):
    script = test_bash_script_error()
    script += """
        sed -i 's/slave-priority {}/slave-priority {}/g' /data/redis.conf
    """.format(original_value, final_value)
    script = build_context_script({}, script)
    host.ssh.run_script(script)


def change_slave_priority_instance(instance, final_value):
    client = instance.databaseinfra.get_driver().get_client(instance)
    client.config_set("slave-priority", final_value)


def reset_sentinel(host, sentinel_host, sentinel_port, service_name):
    LOG.info('Reseting Sentinel {}:{}'.format(sentinel_host, sentinel_port))
    script = test_bash_script_error()
    script += """
        /usr/local/redis/src/redis-cli -h {} -p {} <<EOF_DBAAS
        SENTINEL reset {}
        exit
        \nEOF_DBAAS
        die_if_error "Error reseting sentinel"
    """.format(sentinel_host, sentinel_port, service_name)
    script = build_context_script({}, script)
    host.ssh.run_script(script)


def failover_sentinel(host, sentinel_host, sentinel_port, service_name):
    LOG.info('Failover of Sentinel {}:{}'.format(sentinel_host, sentinel_port))
    script = test_bash_script_error()
    script += """
        /usr/local/redis/src/redis-cli -h {} -p {} <<EOF_DBAAS
        SENTINEL failover {}
        exit
        \nEOF_DBAAS
        die_if_error "Error reseting sentinel"
    """.format(sentinel_host, sentinel_port, service_name)
    script = build_context_script({}, script)
    host.ssh.run_script(script)
