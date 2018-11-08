#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}


create_telegraf_init()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating telegraf init script"

(cat <<EOF_METRIC_DBAAS
#! /usr/bin/env bash

# chkconfig: 2345 99 01
# description: Telegraf daemon

### BEGIN INIT INFO
# Provides:          telegraf
# Required-Start:    \$all
# Required-Stop:     \$remote_fs \$syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start telegraf at boot time
### END INIT INFO

# this init script supports three different variations:
#  1. New lsb that define start-stop-daemon
#  2. Old lsb that don't have start-stop-daemon but define, log, pidofproc and killproc
#  3. Centos installations without lsb-core installed
#
# In the third case we have to define our own functions which are very dumb
# and expect the args to be positioned correctly.

# Command-line options that can be set in /etc/default/telegraf.  These will override
# any config file values.
TELEGRAF_OPTS=

USER=telegraf
GROUP=telegraf

if [ -r /lib/lsb/init-functions ]; then
    source /lib/lsb/init-functions
fi

DEFAULT=/etc/default/telegraf

if [ -r \$DEFAULT ]; then
    set -o allexport
    source \$DEFAULT
    set +o allexport
fi

if [ -z "\$STDOUT" ]; then
    STDOUT=/dev/null
fi
if [ ! -f "\$STDOUT" ]; then
    mkdir -p \`dirname \$STDOUT\`
fi

if [ -z "\$STDERR" ]; then
    STDERR=/var/log/telegraf/telegraf.log
fi
if [ ! -f "\$STDERR" ]; then
    mkdir -p \`dirname \$STDERR\`
fi

OPEN_FILE_LIMIT=65536

function pidofproc() {
    if [ \$# -ne 3 ]; then
        echo "Expected three arguments, e.g. \$0 -p pidfile daemon-name"
    fi

    if [ ! -f "\$2" ]; then
        return 1
    fi

    local pidfile=\`cat \$2\`

    if [ "x\$pidfile" == "x" ]; then
        return 1
    fi

    if ps --pid "\$pidfile" | grep -q \$(basename \$3); then
        return 0
    fi

    return 1
}

function killproc() {
    if [ \$# -ne 3 ]; then
        echo "Expected three arguments, e.g. \$0 -p pidfile signal"
    fi

    pid=\`cat \$2\`

    kill -s \$3 \$pid
}

function log_failure_msg() {
    echo "\$@" "[ FAILED ]"
}

function log_success_msg() {
    echo "\$@" "[ OK ]"
}

# Process name ( For display )
name=telegraf

# Daemon name, where is the actual executable
daemon=/usr/bin/telegraf

# pid file for the daemon
pidfile=/var/run/telegraf/telegraf.pid
piddir=\`dirname \$pidfile\`

if [ ! -d "\$piddir" ]; then
    mkdir -p \$piddir
    chown \$USER:\$GROUP \$piddir
fi

# Configuration file
config=/etc/telegraf/telegraf.conf
confdir=/etc/telegraf/telegraf.d

# If the daemon is not there, then exit.
[ -x \$daemon ] || exit 5

case \$1 in
    start)
        # Checked the PID file exists and check the actual status of process
        if [ -e \$pidfile ]; then
            pidofproc -p \$pidfile \$daemon > /dev/null 2>&1 && status="0" || status="\$?"
            # If the status is SUCCESS then don't need to start again.
            if [ "x\$status" = "x0" ]; then
                log_failure_msg "\$name process is running"
                exit 0 # Exit
            fi
        fi

        # Bump the file limits, before launching the daemon. These will carry over to
        # launched processes.
        ulimit -n \$OPEN_FILE_LIMIT
        if [ \$? -ne 0 ]; then
            log_failure_msg "set open file limit to \$OPEN_FILE_LIMIT"
        fi

        log_success_msg "Starting the process" "\$name"
        if command -v startproc >/dev/null; then
            startproc -u "\$USER" -g "\$GROUP" -p "\$pidfile" -q -- "\$daemon" -pidfile "\$pidfile" -config "\$config" -config-directory "\$confdir" \$TELEGRAF_OPTS
        elif which start-stop-daemon > /dev/null 2>&1; then
            start-stop-daemon --chuid \$USER:\$GROUP --start --quiet --pidfile \$pidfile --exec \$daemon -- -pidfile \$pidfile -config \$config -config-directory \$confdir \$TELEGRAF_OPTS >>\$STDOUT 2>>\$STDERR &
        else
            su -s /bin/sh -c "nohup \$daemon -pidfile \$pidfile -config \$config -config-directory \$confdir \$TELEGRAF_OPTS >>\$STDOUT 2>>\$STDERR &" \$USER
        fi
        log_success_msg "\$name process was started"
        ;;

    stop)
        # Stop the daemon.
        if [ -e \$pidfile ]; then
            pidofproc -p \$pidfile \$daemon > /dev/null 2>&1 && status="0" || status="\$?"
            if [ "\$status" = 0 ]; then
                if killproc -p \$pidfile SIGTERM && /bin/rm -rf \$pidfile; then
                    log_success_msg "\$name process was stopped"
                else
                    log_failure_msg "\$name failed to stop service"
                fi
            fi
        else
            log_failure_msg "\$name process is not running"
        fi
        # Check is is really stopped
        command="/usr/bin/telegraf"
        if ps ax | grep -v grep | grep \$command > /dev/null
        then
            log_failure_msg "\$name is still running. Sleep 2 seconds and force stop with kill"
            sleep 2
            if ps ax | grep -v grep | grep \$command > /dev/null
            then
                ps -ef | grep -v grep | grep "/usr/bin/telegraf" | awk '{print \$2}' | xargs kill -9
            fi
        fi
        ;;

    reload)
        # Reload the daemon.
        if [ -e \$pidfile ]; then
            pidofproc -p \$pidfile \$daemon > /dev/null 2>&1 && status="0" || status="\$?"
            if [ "\$status" = 0 ]; then
                if killproc -p \$pidfile SIGHUP; then
                    log_success_msg "\$name process was reloaded"
                else
                    log_failure_msg "\$name failed to reload service"
                fi
            fi
        else
            log_failure_msg "\$name process is not running"
        fi
        ;;

    restart)
        # Restart the daemon.
        \$0 stop && sleep 2 && \$0 start
        ;;

    status)
        # Check the status of the process.
        if [ -e \$pidfile ]; then
            if pidofproc -p \$pidfile \$daemon > /dev/null; then
                log_success_msg "\$name Process is running"
                exit 0
            else
                log_failure_msg "\$name Process is not running"
                exit 1
            fi
        else
            log_failure_msg "\$name Process is not running"
            exit 3
        fi
        ;;

    version)
        \$daemon version
        ;;

    *)
        # For invalid arguments, print the usage message.
        echo "Usage: \$0 {start|stop|restart|status|version}"
        exit 2
        ;;
esac
EOF_METRIC_DBAAS
) > /etc/init.d/telegraf
    die_if_error "Error setting telegraf init script"
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
  brokers =[{{KAFKA_ENDPOINT|safe}}]
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
  create_telegraf_init
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

