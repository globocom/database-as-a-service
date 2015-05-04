# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


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


def get_replication_info(instance):
    client = get_client(instance)

    client.query('show master status')
    r = client.store_result()
    row = r.fetch_row(maxrows=0, how=1)
    return row[0]['File'], row[0]['Position']


def change_master_to(instance, master_host, bin_log_file, bin_log_position):
    client = get_client(instance)
    client.query('stop slave')

    sql_command = "change master to master_host='{}', master_log_file='{}', master_log_pos={}"
    sql_command = sql_command.format(master_host, bin_log_file, bin_log_position)
    client.query(sql_command)

    client.query('start slave')


def build_flipper_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Setting /etc/hosts file"
        echo "\n{{VIP_FLIPPER}}      flipper-metadata\n{{IPWRITE}}         heartbeat\n" >> /etc/hosts

        echo ""; echo $(date "+%Y-%m-%d %T") "- Adding hosts to flipper known_hosts file"
        ssh-keyscan -t rsa {{HOST01.address}} >> /home/flipper/.ssh/known_hosts
        ssh-keyscan -t rsa {{HOST02.address}} >> /home/flipper/.ssh/known_hosts
        chown flipper:flipper /home/flipper/.ssh/known_hosts
    """
