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

    connect_string = databaseinfra.get_driver().get_replica_name() + \
        "/" + connect_string

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


def build_start_database_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
        /etc/init.d/mongodb start > /dev/null
        die_if_error "Error starting database"
    """


def build_stop_database_script():
    return """
        /etc/init.d/mongodb stop
        rm -rf /data/*
    """


def build_add_replica_set_members_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Adding new database members"
        /usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS
        rs.add( { "_id": {{SECUNDARY_ONE_MEMBER_ID}}, "host": "{{SECUNDARY_ONE}}", "priority": 0 } )
        rs.add( { "_id": {{SECUNDARY_TWO_MEMBER_ID}}, "host": "{{SECUNDARY_TWO}}", "priority": 0 } )
        rs.addArb("{{ARBITER}}")
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
       cfg.members[3].priority = 1
       cfg.members[4].priority = 1
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
       cfg.members[1].priority = 0
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
       cfg.members[0].priority = 1
       cfg.members[1].priority = 1
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
       cfg.members[4].priority = 0
       rs.reconfig(cfg)
       exit
       \nEOF_DBAAS
       die_if_error "Error changing priority of members"
    """
