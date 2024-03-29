# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def build_mongodb_instance_connect_string(instance):
    databaseinfra = instance.databaseinfra
    return "{}:{}/admin -u{} -p{}".format(
        instance.address, instance.port,
        databaseinfra.user, databaseinfra.password)


def build_change_release_alias_script():
    return """
        cd {{TARGET_PATH}}
        die_if_error "Error change current path"

        rm -f mongodb
        die_if_error "Error deleting mongodb alias"

        ln -s {{MONGODB_RELEASE_FOLDER}} mongodb
        die_if_error "Error creating mongodb alias"
    """


def build_add_replica_set_member_script(mongodb_version, readonly, arbiter):
    readonly_params = ',"priority": 0, "votes": 0' if readonly else ''
    arbiter_params = ',"arbiterOnly": true' if arbiter else ''
    replica_id_string = '"_id": {{REPLICA_ID}}, ' if mongodb_version < '3.0.0' else ''
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Adding new database members"
        /usr/local/mongodb/bin/mongo --host {{CONNECT_ADMIN_URI}} {{SSL_CONN_STRING}} <<EOF_DBAAS
        rs.add( { """ + replica_id_string + """
            "host": "{{HOSTADDRESS}}:{{PORT}}" """ + readonly_params + arbiter_params + """} )
        exit
        \nEOF_DBAAS
        die_if_error "Error adding new replica set members"
    """


def build_remove_read_only_replica_set_member_script():
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"
        /usr/local/mongodb/bin/mongo --host {{CONNECT_ADMIN_URI}} {{SSL_CONN_STRING}} <<EOF_DBAAS
        rs.remove( "{{HOSTADDRESS}}:{{PORT}}")
        exit
        \nEOF_DBAAS
        die_if_error "Error adding new replica set members"
    """


def build_change_oplogsize_script(instance, oplogsize):
    connect_string = build_mongodb_instance_connect_string(instance)
    return """
        /usr/local/mongodb/bin/mongo %(connect_string)s <<EOF_DBAAS
        use local
        db = db.getSiblingDB('local')
        db.temp.drop()
        db.temp.save( db.oplog.rs.find( { }, { ts: 1, h: 1 } ).sort( {\$natural : -1} ).limit(1).next() )
        db.oplog.rs.drop()
        db.runCommand( { create: "oplog.rs", capped: true, size: ( %(oplogsize)s * 1024 * 1024) } )
        db.oplog.rs.save( db.temp.findOne() )
        db.oplog.rs.find()
        exit
        \nEOF_DBAAS
    """ % {'connect_string': connect_string, 'oplogsize': oplogsize}


def build_change_priority_script(size):
    config = ""
    for index in range(size):
        config += "cfg.members[{index}].priority = (cfg.members[{index}].host == \"{host_field}\" ? {priority_field} : cfg.members[{index}].priority)\n".format(
            index=index, host_field="{{HOST_ADDRESS}}",
            priority_field="{{PRIORITY}}"
        )
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Change member priority"
        /usr/local/mongodb/bin/mongo --host {{CONNECT_ADMIN_URI}} {{SSL_CONN_STRING}} <<EOF_DBAAS
        cfg = rs.conf()
        """ + config + """
        rs.reconfig(cfg)
        exit
        \nEOF_DBAAS
        die_if_error "Error adding new replica set members"
    """
