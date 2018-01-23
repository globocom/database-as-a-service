# -*- coding: utf-8 -*-
import logging
from util import build_context_script, exec_remote_command_host
from workflow.steps.util import test_bash_script_error

LOG = logging.getLogger(__name__)


def build_permission_script():

    return """
        mkdir /data/data
        die_if_error "Error creating data dir"

        chown redis:redis /data
        die_if_error "Error changing datadir permission"
        chown -R redis:redis /data/data
        die_if_error "Error changing datadir permission"
        chmod g+r /data
        die_if_error "Error changing datadir permission"
        chmod g+x /data
        die_if_error "Error changing datadir permission"
        """


def build_clean_database_dir_script():
    return """
        /etc/init.d/redis stop
        rm -rf /data/*
    """


def build_start_stop_scripts():
    return """
        stopdatabase() {
            /etc/init.d/redis stop
            die_if_error "Error stopping database"
        }

        startdatabase() {
            /etc/init.d/redis start
            die_if_error "Error starting database"
        }

        stopsentinel() {
            /etc/init.d/sentinel stop
            die_if_error "Error stopping sentinel"
        }

        startsentinel() {
            /etc/init.d/sentinel start
            die_if_error "Error starting sentinel"
        }

        restart_http() {
            /etc/init.d/httpd stop > /dev/null
            die_if_error "Error stopping httpd"
            /etc/init.d/httpd start > /dev/null
            die_if_error "Error starting httpd"
        }

    """


def build_start_database_script():
    return """
        startdatabase
    """


def build_stop_database_script():
    return """
        stopdatabase
    """


def build_start_sentinel_script():
    return """
        startsentinel
    """


def build_stop_sentinel_script():
    return """
        stopsentinel
    """


def build_start_http_script():
    return """
        restart_http
    """


def change_slave_priority_file(host, original_value, final_value):
    script = test_bash_script_error()
    script += """
        sed -i 's/slave-priority {}/slave-priority {}/g' /data/redis.conf
    """.format(original_value, final_value)
    script = build_context_script({}, script)
    output = {}
    return_code = exec_remote_command_host(host, script, output)
    LOG.info(output)
    if return_code != 0:
        raise Exception(str(output))


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
    output = {}
    return_code = exec_remote_command_host(host, script, output)
    LOG.info(output)
    if return_code != 0:
        raise Exception(str(output))


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
    output = {}
    return_code = exec_remote_command_host(host, script, output)
    LOG.info(output)
    if return_code != 0:
        raise Exception(str(output))
