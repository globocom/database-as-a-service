# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def build_mongodb_connect_string(instances, databaseinfra):
    connect_string = ""
    for instance in instances:
        if instance.instance_type != instance.MONGODB_ARBITER:
            if connect_string:
                connect_string += ','
            connect_string += instance.address + \
                ":" + str(instance.port)

    replica_name = databaseinfra.get_driver().get_replica_name()
    if replica_name:
        connect_string = replica_name + "/" + connect_string

    connect_string = " --host {} admin -u{} -p{}".format(
        connect_string, databaseinfra.user, databaseinfra.password)

    LOG.debug(connect_string)
    return connect_string


def build_permission_script():

    return """
        mkdir /data/data
        die_if_error "Error creating data dir"

        chown mongodb:mongodb /data
        die_if_error "Error changing datadir permission"
        chown -R mongodb:mongodb /data/*
        die_if_error "Error changing datadir permission"

        chmod 600 /data/mongodb.key
        die_if_error "Error changing mongodb key file permission"
        """


def build_start_database_script(wait_time=0):
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mongodb start > /dev/null
        die_if_error "Error starting database"
        sleep {}
    """.format(wait_time)


def build_stop_database_script(clean_data=True):
    script = """
        /etc/init.d/mongodb stop
        sleep 5
    """
    if clean_data:
        script += """
            rm -rf /data/*
        """
    return script


def build_add_replica_set_members_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Adding new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.add( { "_id": {{SECUNDARY_ONE_MEMBER_ID}}, "host": "{{SECUNDARY_ONE}}", "priority": 0, "hidden": true } )
        rs.add( { "_id": {{SECUNDARY_TWO_MEMBER_ID}}, "host": "{{SECUNDARY_TWO}}", "priority": 0, "hidden": true } )
        rs.add( { "_id": {{ARBITER_MEMBER_ID}}, "host": "{{ARBITER}}", "priority": 0, "hidden": true, "arbiterOnly": true } )
        exit
        \nEOF_DBAAS
        die_if_error "Error adding new replica set members"
    """


def build_remove_replica_set_members_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{ARBITER}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"

        sleep 30
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{SECUNDARY_TWO}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"

        sleep 30
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.remove("{{SECUNDARY_ONE}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error removing new replica set members"
    """


def build_switch_primary_to_new_instances_script():
    return """
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       status = rs.status()
       var_secundary_member = 0
       if (status["members"][1].stateStr == "SECONDARY") {var_secundary_member = 1}
       cfg = rs.conf()
       cfg.members[var_secundary_member].priority = 0
       cfg.members[var_secundary_member].hidden = true
       cfg.members[2].priority = 0
       cfg.members[2].hidden = true
       cfg.members[3].priority = 1
       cfg.members[3].hidden = false
       cfg.members[4].priority = 1
       cfg.members[4].hidden = false
       cfg.members[5].priority = 1
       cfg.members[5].hidden = false
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       rs.stepDown()
       exit
       \nEOF_DBAAS
       die_if_error "Error switching primary"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       cfg = rs.conf()
       cfg.members[0].priority = 0
       cfg.members[0].hidden = true
       cfg.members[1].priority = 0
       cfg.members[1].hidden = true
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"
    """


def build_switch_primary_to_old_instances_script():
    return """
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       status = rs.status()
       var_secundary_member = 3
       if (status["members"][4].stateStr == "SECONDARY") {var_secundary_member = 4}
       cfg = rs.conf()
       cfg.members[var_secundary_member].priority = 0
       cfg.members[var_secundary_member].hidden = true
       cfg.members[0].priority = 1
       cfg.members[0].hidden = false
       cfg.members[1].priority = 1
       cfg.members[1].hidden = false
       cfg.members[2].priority = 1
       cfg.members[2].hidden = false
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       rs.stepDown()
       exit
       \nEOF_DBAAS
       die_if_error "Error switching primary"

       sleep 30
       echo ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"
       /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
       cfg = rs.conf()
       cfg.members[3].priority = 0
       cfg.members[3].hidden = true
       cfg.members[4].priority = 0
       cfg.members[4].hidden = true
       cfg.members[5].priority = 0
       cfg.members[5].hidden = true
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"
    """


def clean_files_old_binary_files():
    return """
        cd {{TARGET_PATH}}
        rm -rf {{MONGODB_OLD_RELEASE_FOLDER}}
    """


def build_cp_mongodb_binary_file():
    return """
        cd {{TARGET_PATH}}
        die_if_error "Error change current path"

        cp {{SOURCE_PATH}}/{{MONGODB_RELEASE_FILE}} .
        die_if_error "Error coping mongodb binary file"

        tar -xvf {{MONGODB_RELEASE_FILE}}
        die_if_error "Error uncompress mongodb binary file"

        chown -R mongodb:mongodb {{MONGODB_RELEASE_FOLDER}}
        die_if_error "Error changing owner"

        rm -f {{MONGODB_RELEASE_FILE}}
        die_if_error "Error removing tgz file"
    """


def build_change_release_alias_script():
    return """
        cd {{TARGET_PATH}}
        die_if_error "Error change current path"

        rm -f mongodb
        die_if_error "Error deleting mongodb alias"

        ln -s {{MONGODB_RELEASE_FOLDER}} mongodb
        die_if_error "Error creating mongodb alias"
    """


def build_authschemaupgrade_script():
    return """
        sleep 10
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        db.adminCommand({authSchemaUpgrade: 1});
        exit
        \nEOF_DBAAS
        die_if_error "Error running authSchemaUpgrade"
    """


def build_change_limits_script():
    return """
        sed -i 's/soft nofile 32756/soft nofile 65536/g' /etc/security/limits.conf
        echo "* - nproc 65536" >> /etc/security/limits.conf
    """


def build_disable_authentication_single_instance_script():
    return """
        sed -i 's/auth/#auth/g' /data/mongodb.conf
    """


def build_enable_authentication_single_instance_script():
    return """
        sed -i 's/#auth/auth/g' /data/mongodb.conf
    """


def build_wait_admin_be_created_script():
    return """
        while true
        do
           if [ -d "/data/data/admin" ]; then
              break
           fi
           sleep 10
        done
        sleep 60
    """


def build_restart_database_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mongodb restart > /dev/null
        die_if_error "Error restarting database"
    """


def build_clean_data_data_script():
    return """
        rm -rf /data/data/*
    """


def build_dump_database_script():
    return """
        mkdir /data/dump
        /usr/local/mongodb/bin/mongodump --out /data/dump/
        die_if_error "Error dumping database"
    """


def build_mongorestore_database_script():
    return """
        /usr/local/mongodb/bin/mongorestore /data/dump/
        die_if_error "Error restoring database"
        rm -rf /data/dump/
    """


def build_change_mongodb_conf_file_script():
    return """
        line=$(cat '/data/mongodb.conf' | grep -n 'dbpath' | grep -o '^[0-9]*')
        line=$((line + 2))
        sed -i ${line}'i\# Storage Engine\\nstorageEngine = wiredTiger\\n' /data/mongodb.conf

        line=$(cat '/data/mongodb.conf' | grep -n 'rest' | grep -o '^[0-9]*')
        line=$((line + 1))
        sed -i ${line}'i\httpinterface = true' /data/mongodb.conf
    """


def build_remove_reprecated_index_counter_metrics():
    return """
        sed -i '271,314 d' /etc/td-agent/td-agent.conf
        sleep 20
        /etc/init.d/td-agent start
    """
