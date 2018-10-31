#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

create_telegraf_default()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf default file"

(cat <<EOF_METRIC_DBAAS
DBUSER={{USER}}
DBPASS={{PASSWORD}}
LOCALHOST=127.0.0.1
HOST={{HOSTADDRESS}}
PORT={{PORT}}
EOF_METRIC_DBAAS
) > /etc/default/telegraf
    die_if_error "Error setting telegraf default file"
}


create_telegraf_config()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf config file"

(cat <<EOF_METRIC_DBAAS
###############################################################################
#                            agent                                   #
###############################################################################
[agent]
  interval = "1m"
  round_interval = true
  flush_interval = "10s"

  metric_batch_size = 3000
  metric_buffer_limit = 1000000

  hostname = "{{HOSTNAME}}"
  omit_hostname = false

  collection_jitter = "0s"
  flush_jitter = "0s"
  precision = ""
  debug = true
  quiet = false
  logfile = ""


###############################################################################
#                            OUTPUT PLUGINS                                   #
###############################################################################

[[outputs.kafka]]
  brokers =["{{KAFKA_ENDPOINT}}"]
  topic = "{{KAFKA_TOPIC}}"
  compression_codec = 0
  required_acks = -1
  max_retry = 10
  data_format = "influx"

###############################################################################
#                            SERVICE INPUT PLUGINS                            #
###############################################################################

[[inputs.cpu]]
  percpu = true
  totalcpu = true
  collect_cpu_time = true
  report_active = false
  taginclude = ["cpu", "host"]
  fieldpass = ["usage_guest", "usage_guest_nice", "usage_idle", "usage_iowait", "usage_irq", "usage_nice", "usage_softirq", "usage_steal", "usage_system", "usage_user"]

[[inputs.mem]]
  taginclude = ["host"]
  fieldpass = ["active", "available", "available_percent", "buffered", "cached", "free", "inactive", "total", "used", "used_percent"]

[[inputs.swap]]
  taginclude = ["host"]
  fieldpass = ["free", "total", "used", "used_percent"]

[[inputs.disk]]
  mount_points = ["/", "/data"]
  ignore_fs = ["tmpfs", "rootfs"]
  taginclude = ["host", "device", "fstype", "mode", "path"]
  fieldpass = ["free", "total", "used", "used_percent"]

[[inputs.system]]
  taginclude = ["host"]
  fieldpass = ["load1", "load5", "load15", "n_users", "n_cpus"]

[[inputs.net]]
  interfaces = ["eth*"]
  ignore_protocol_stats = true
  taginclude = ["host", "interface"]
  fieldpass = ["bytes_recv", "bytes_sent", "err_in", "err_out"]


EOF_METRIC_DBAAS
) > /etc/telegraf/telegraf.conf
    die_if_error "Error setting telegraf config file"
}


create_mysql_telegraf_config()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf config file"

(cat <<EOF_METRIC_DBAAS
[[inputs.mysql]]
  servers = ["\$DBUSER:\$DBPASS@tcp(\$LOCALHOST:\$PORT)/?tls=false"]
  taginclude = ["host"]
  fieldpass = ["bytes_received", "bytes_sent", "com_commit", "com_delete", "com_insert", "com_select", "com_update", "qcache_free_blocks", "qcache_free_memory", "qcache_hits", "qcache_inserts", "qcache_not_cached", "qcache_queries_in_cache", "qcache_total_blocks", "table_locks_immediate", "table_locks_waited", "table_open_cache_hits", "table_open_cache_misses", "table_open_cache_overflows", "threads_connected", "threads_running"]

  ## Selects the metric output format.
  ##
  ## This option exists to maintain backwards compatibility, if you have
  ## existing metrics do not set or change this value until you are ready to
  ## migrate to the new format.
  ##
  ## If you do not have existing metrics from this plugin set to the latest
  ## version.
  ##
  ## Telegraf >=1.6: metric_version = 2
  ##           <1.6: metric_version = 1 (or unset)
  metric_version = 2

  ## the limits for metrics form perf_events_statements
  #perf_events_statements_digest_text_limit  = 120
  #perf_events_statements_limit              = 250
  #perf_events_statements_time_limit         = 86400
  #
  ## if the list is empty, then metrics are gathered from all databasee tables
  table_schema_databases                    = []
  #
  ## gather metrics from INFORMATION_SCHEMA.TABLES for databases provided above list
  gather_table_schema                       = true
  #
  ## gather thread state counts from INFORMATION_SCHEMA.PROCESSLIST
  gather_process_list                       = true
  #
  ## gather user statistics from INFORMATION_SCHEMA.USER_STATISTICS
  gather_user_statistics                    = false
  #
  ## gather auto_increment columns and max values from information schema
  gather_info_schema_auto_inc               = true
  #
  ## gather metrics from INFORMATION_SCHEMA.INNODB_METRICS
  gather_innodb_metrics                     = true
  #
  ## gather metrics from SHOW SLAVE STATUS command output
  gather_slave_status                       = true
  #
  ## gather metrics from SHOW BINARY LOGS command output
  gather_binary_logs                        = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.TABLE_IO_WAITS_SUMMARY_BY_TABLE
  gather_table_io_waits                     = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.TABLE_LOCK_WAITS
  gather_table_lock_waits                   = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.TABLE_IO_WAITS_SUMMARY_BY_INDEX_USAGE
  gather_index_io_waits                     = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.EVENT_WAITS
  gather_event_waits                        = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.FILE_SUMMARY_BY_EVENT_NAME
  gather_file_events_stats                  = true
  #
  ## gather metrics from PERFORMANCE_SCHEMA.EVENTS_STATEMENTS_SUMMARY_BY_DIGEST
  gather_perf_events_statements             = true
  #
  ## Some queries we may want to run less often (such as SHOW GLOBAL VARIABLES)
  interval_slow                   = "30m"
EOF_METRIC_DBAAS
) >> /etc/telegraf/telegraf.conf
    die_if_error "Error setting telegraf config file"
}

create_mongodb_telegraf_config()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf config file"

(cat <<EOF_METRIC_DBAAS
[[inputs.mongodb]]
  servers = ["mongodb://\$DBUSER:\$DBPASS@\$LOCALHOST:\$PORT"]
  gather_perdb_stats = true
  taginclude = ["host", "db_name"]
  fieldpass = ["commands_per_sec", "connections_available", "connections_current", "deletes_per_sec", "flushes_per_sec", "getmores_per_sec", "inserts_per_sec", "queries_per_sec", "resident_megabytes", "updates_per_sec", "vsize_megabytes", "avg_obj_size", "collections", "data_size", "index_size", "indexes", "num_extents", "objects", "ok", "storage_size", "type"]
EOF_METRIC_DBAAS
) >> /etc/telegraf/telegraf.conf
    die_if_error "Error setting telegraf config file"
}

create_redis_telegraf_config()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf config file"

(cat <<EOF_METRIC_DBAAS
[[inputs.redis]]
  servers = ["tcp://:\$DBPASS@\$HOST:\$PORT"]
  taginclude = ["host", "database"]
  fieldpass = ["blocked_clients", "clients", "keyspace_hits", "keyspace_misses", "maxmemory", "used_cpu_sys", "used_cpu_sys_children", "used_cpu_user", "used_cpu_user_children", "used_memory", "expires", "keys"]
EOF_METRIC_DBAAS
) >> /etc/telegraf/telegraf.conf
    die_if_error "Error setting telegraf config file"
}


{% if CREATE_TELEGRAF_CONFIG %}
  create_telegraf_config
{% endif %}

{% if CREATE_DEFAULT_FILE %}
  create_telegraf_default
{% endif %}

{% if MYSQL %}
  create_mysql_telegraf_config
{% endif %}

{% if MONGODB %}
  create_mongodb_telegraf_config
{% endif %}

{% if REDIS %}
  create_redis_telegraf_config
{% endif %}

