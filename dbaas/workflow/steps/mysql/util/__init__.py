# -*- coding: utf-8 -*-
import logging
from time import sleep
from util import exec_remote_command_host

LOG = logging.getLogger(__name__)


def build_uncomment_skip_slave_script():

    return """
        sed -e 's/^#skip_slave_start/skip_slave_start/' -i /etc/my.cnf
        """


def build_comment_skip_slave_script():

    return """
        sed -e 's/^skip_slave_start/#skip_slave_start/' -i /etc/my.cnf
        """


def build_permission_script():

    return """
        chown mysql:mysql /data
        die_if_error "Error changing datadir permission"
        chown -R mysql:mysql /data/*
        die_if_error "Error changing datadir permission"
        """


def build_server_id_conf_script():
    return """
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the server id db file"
    \n(cat <<EOF_DBAAS
    \n[mysqld]
    \nserver_id={{SERVERID}}
    \nEOF_DBAAS
    \n) >  /etc/server_id.cnf
    """


def build_start_database_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mysql start > /dev/null
        die_if_error "Error starting database"
    """


def build_stop_database_script():
    return """
        /etc/init.d/mysql stop
        rm -rf /data/*
    """


def build_mount_snapshot_volume_script():
    return """
        mkdir /data2

        mount -t nfs -o bg,intr {{EXPORT_PATH}} /data2
        die_if_error "Error mounting volume"

        cp -rp /data2/.snapshot/{{SNAPSHOPT_NAME}}/* /data/
        die_if_error "Error coping datafiles"

        umount /data2
        rm -rf /data2

    """


def build_remove_deprecated_files_script():
    return """
        rm -f /data/data/auto.cnf
        rm -f /data/data/*.err
        rm -f /data/data/*.pid
    """


def get_client(instance):
    databaseinfra = instance.databaseinfra
    driver = databaseinfra.get_driver()

    return driver.get_client(instance)


def get_client_for_infra(databaseinfra):
    driver = databaseinfra.get_driver()

    return driver.get_client(None)


def get_replication_info(instance):
    client = get_client(instance)

    client.query('show master status')
    r = client.store_result()
    row = r.fetch_row(maxrows=0, how=1)
    return row[0]['File'], row[0]['Position']


def check_seconds_behind(instance, retries=50):
    client = get_client(instance)

    for attempt in range(retries):
        LOG.info("Checking replication %i on %s " % (attempt + 1, instance))

        client.query("show slave status")
        r = client.store_result()
        row = r.fetch_row(maxrows=0, how=1)
        seconds_behind = row[0]['Seconds_Behind_Master']

        if seconds_behind is None:
            raise Exception("Replication is not running")

        if seconds_behind == '0':
            return True

        if attempt == retries - 1:
            LOG.warning("Seconds behind: {}".format(seconds_behind))
            return False

        sleep(10)


def change_master_to(instance, master_host, bin_log_file, bin_log_position):
    client = get_client(instance)
    client.query('stop slave')

    sql_command = "change master to master_host='{}', master_log_file='{}', master_log_pos={}"
    sql_command = sql_command.format(
        master_host, bin_log_file, bin_log_position)
    client.query(sql_command)

    client.query('start slave')


def build_mk_heartbeat_daemon_script(option='start'):
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting mk-heartbeat-daemon"
        /etc/init.d/mk-heartbeat-daemon {} > /dev/null
        """.format(option)


def get_replication_information_from_file(host,):
    command = 'cat /data/data/mysql_binlog_master_file_pos'
    output = {}
    return_code = exec_remote_command_host(host, command, output)
    if return_code != 0:
        raise Exception("Could not read file: {}".format(output))

    replication_file, replication_position = parse_replication_info(
        output['stdout'][0])

    return replication_file, replication_position


def parse_replication_info(replication_info):
    split_vars = replication_info.split(';')
    replication_file = split_var_and_value(split_vars[0])
    replication_position = split_vars[1]

    position_end_with_new_line = replication_position.find('\n')
    if position_end_with_new_line:
        replication_position = replication_position[
            :position_end_with_new_line]

    replication_position = split_var_and_value(replication_position)

    return replication_file, replication_position


def split_var_and_value(info):
    return info.split('=')[1]


def start_slave(instance):
    client = get_client(instance)
    client.query("start slave")
