#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

createconfigdbfile()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the database config file"

(cat <<EOF_DBAAS
[mysqld_safe]
syslog

[heartbeat]
host=heartbeat
database=heartbeat
user=heartbeat
password=pulse

[client]
port                            = 3306
socket                          = /var/lib/mysql/mysql.sock

[mysql]
no_auto_rehash

[mysqld]
{% if SSL_CONFIGURED %}
ssl                             = ON
ssl-ca                          = {{ INFRA_SSL_CA }}
ssl-cert                        = {{ INFRA_SSL_CERT }}
ssl-key                         = {{ INFRA_SSL_KEY }}
{% endif %}

binlog_format                   = {{ configuration.binlog_format.value }}
performance_schema              = {{ configuration.performance_schema.value }}
transaction_isolation           = {{ configuration.transaction_isolation.value }}

port                            = 3306
socket                          = /var/lib/mysql/mysql.sock
datadir                         = /data/data
tmpdir                          = /data/tmp/

skip_external_locking           = {{ configuration.skip_external_locking.value }}
skip_name_resolve               = {{ configuration.skip_name_resolve.value }}

default_storage_engine          = {{ configuration.default_storage_engine.value }}
default_tmp_storage_engine      = {{ configuration.default_tmp_storage_engine.value }}

character_set_server            = {{ configuration.character_set_server.value }}

max_connections                 = {{ configuration.max_connections.value }}
max_connect_errors              = {{ configuration.max_connect_errors.value }}

thread_cache_size               = {{ configuration.thread_cache_size.value }}
table_open_cache                = {{ configuration.table_open_cache.value }}

query_cache_type                = {{ configuration.query_cache_type.value }}
query_cache_size                = {{ configuration.query_cache_size.value }}

thread_stack                    = {{ configuration.thread_stack.value }}
thread_concurrency              = {{ configuration.thread_concurrency.value }}

max_allowed_packet              = {{ configuration.max_allowed_packet.value }}
sort_buffer_size                = {{ configuration.sort_buffer_size.value }}

tmp_table_size                  = {{ configuration.tmp_table_size.value }}
max_heap_table_size             = {{ configuration.max_heap_table_size.value }}

wait_timeout                    = {{ configuration.wait_timeout.value }}
interactive_timeout             = {{ configuration.interactive_timeout.value }}
log_bin_trust_function_creators = {{ configuration.log_bin_trust_function_creators.value }}

# Dual Master
read_only                       = 1
#skip_slave_start                = 1

# Binary Logging
log_bin                         = /data/repl/mysql-bin
relay_log                       = /data/repl/mysql-relay
sync_binlog                     = {{ configuration.sync_binlog.value }}
expire_logs_days                = {{ configuration.expire_logs_days.value }}
max_binlog_size                 = {{ configuration.max_binlog_size.value }}
log_slave_updates               = {{ configuration.log_slave_updates.value }}

# Slow Query Logging
slow_query_log_file             = /data/logs/mysql-slow.log
long_query_time                 = {{ configuration.long_query_time.value }}
slow_query_log                  = {{ configuration.slow_query_log.value }}

# MyISAM
key_buffer_size                 = {{ configuration.key_buffer_size.value }}
myisam_sort_buffer_size         = {{ configuration.myisam_sort_buffer_size.value }}
read_buffer_size                = {{ configuration.read_buffer_size.value }}
read_rnd_buffer_size            = {{ configuration.read_rnd_buffer_size.value }}

# InnoDB
innodb_data_home_dir            = /data/data
innodb_log_group_home_dir       = /data/data
innodb_data_file_path           = ibdata1:10M:autoextend
innodb_autoextend_increment     = {{ configuration.innodb_autoextend_increment.value }}
innodb_file_per_table           = {{ configuration.innodb_file_per_table.value }}
innodb_buffer_pool_size         = {{ configuration.innodb_buffer_pool_size.value }}
innodb_log_files_in_group       = {{ configuration.innodb_log_files_in_group.value }}
innodb_log_file_size            = {{ configuration.innodb_log_file_size.value }}
innodb_log_buffer_size          = {{ configuration.innodb_log_buffer_size.value }}
innodb_lock_wait_timeout        = {{ configuration.innodb_lock_wait_timeout.value }}
innodb_flush_log_at_trx_commit  = {{ configuration.innodb_flush_log_at_trx_commit.value }}
innodb_flush_method             = {{ configuration.innodb_flush_method.value }}
innodb_thread_concurrency       = {{ configuration.innodb_thread_concurrency.value }}
innodb_max_dirty_pages_pct      = {{ configuration.innodb_max_dirty_pages_pct.value }}
innodb_max_purge_lag            = {{ configuration.innodb_max_purge_lag.value }}

explicit_defaults_for_timestamp = {{ configuration.explicit_defaults_for_timestamp.value }}

!include /etc/server_id.cnf

EOF_DBAAS
) > /etc/my.cnf
    die_if_error "Error setting my.cnf"

}

createserveriddbfile()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the server id db file"

(cat <<EOF_DBAAS
[mysqld]
server_id={{SERVERID}}
EOF_DBAAS
) >  /etc/server_id.cnf
    die_if_error "Error setting server_id file"

}

configure_graylog()
{
    echo "\$EscapeControlCharactersOnReceive off" >> /etc/rsyslog.d/dbaaslog.conf
    sed -i "\$a \$template db-log, \"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%	tags: INFRA,DBAAS,MYSQL,{{DATABASENAME}}\"" /etc/rsyslog.d/dbaaslog.conf
    sed -i "\$a*.*                    @{{ GRAYLOG_ENDPOINT }}; db-log" /etc/rsyslog.d/dbaaslog.conf
    /etc/init.d/rsyslog restart
}


{% if CONFIGFILE_ONLY %}
    createconfigdbfile
{% else %}
    createconfigdbfile
    createserveriddbfile
    configure_graylog
{% endif %}

exit 0
