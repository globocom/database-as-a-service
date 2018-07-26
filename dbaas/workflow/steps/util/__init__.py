# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def test_bash_script_error():
    return """
      #!/bin/bash

      die_if_error()
      {
            local err=$?
            if [ "$err" != "0" ];
            then
                echo "$*"
                exit $err
            fi
      }"""


def monit_script(option='start'):
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Monit"
        /etc/init.d/monit {}
        """.format(option)


def get_backup_log_configuration_dict(environment, databaseinfra):
    from backup.models import LogConfiguration
    from django.core.exceptions import ObjectDoesNotExist

    try:
        log_configuration = LogConfiguration.objects.get(environment=environment,
                                                         engine_type=databaseinfra.engine.engine_type)
    except ObjectDoesNotExist:
        return None

    return {
        'MOUNT_PATH': log_configuration.mount_point_path,
        'BACKUP_LOG_EXPORT_PATH': log_configuration.filer_path,
        'RETENTION_BACKUP_LOG_DAYS': log_configuration.retention_days,
        'DATABASE_LOG_PATH': log_configuration.log_path,
        'BACKUP_LOG_SCRIPT': log_configuration.backup_log_script,
        'CONFIG_BACKUP_LOG_SCRIPT': log_configuration.config_backup_log_script,
        'CLEAN_BACKUP_LOG_SCRIPT': log_configuration.clean_backup_log_script,
        'DATABASEINFRA_NAME': databaseinfra.name,
        'BACKUP_LOG_CRON_MINUTE': log_configuration.cron_minute,
        'BACKUP_LOG_CRON_HOUR': log_configuration.cron_hour,
    }


def build_backup_log_script():
    return """
    mountbackuplogdisk()
    {
        echo ""; echo $(date "+%Y-%m-%d %T") "- Mounting database backup log disk"
        mkdir -p {{MOUNT_PATH}}
        echo "{{BACKUP_LOG_EXPORT_PATH}}    {{MOUNT_PATH}} nfs defaults,bg,intr,nolock 0 0" >> /etc/fstab
        die_if_error "Error setting fstab"
        mount {{MOUNT_PATH}}
        die_if_error "Error mounting database backup log disk"
        wcl=$(mount -l | grep {{MOUNT_PATH}} | grep nfs | wc -l)
        if [ "$wcl" -eq 0 ]
        then
            echo "Could not mount {{MOUNT_PATH}}"
            exit 100
        fi
        mkdir -p {{MOUNT_PATH}}/{{DATABASEINFRA_NAME}}/$(hostname -s)
        die_if_error "Could not create backup log dir"
    }

    createbackuplogfilescript()
    {
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the purge backup log script"

(cat <<EOF_DBAAS_PURGE_BACKUPS
if [ -d "{{MOUNT_PATH}}" ]; then
    rm -rf {{MOUNT_PATH}}/{{DATABASEINFRA_NAME}}
fi
EOF_DBAAS_PURGE_BACKUPS
) > {{CLEAN_BACKUP_LOG_SCRIPT}}
    die_if_error "Error setting {{CLEAN_BACKUP_LOG_SCRIPT}}"
    chmod u+x {{CLEAN_BACKUP_LOG_SCRIPT}}
    die_if_error "Error changing {{CLEAN_BACKUP_LOG_SCRIPT}} permission"

    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the database backup log config file"
(cat <<EOF_DBAAS_BACKUP_LOG_CONFIG
export DATABASE_LOG_PATH="{{DATABASE_LOG_PATH}}"
export DST_PATH="{{MOUNT_PATH}}/{{DATABASEINFRA_NAME}}/$(hostname -s)"
export RETENTION_BACKUP_LOG_DAYS={{RETENTION_BACKUP_LOG_DAYS}}
EOF_DBAAS_BACKUP_LOG_CONFIG
) > {{CONFIG_BACKUP_LOG_SCRIPT}}
    die_if_error "Error setting {{CONFIG_BACKUP_LOG_SCRIPT}}"

    chmod u+x {{CONFIG_BACKUP_LOG_SCRIPT}}
    die_if_error "Error changing {{CONFIG_BACKUP_LOG_SCRIPT}} permission"

(cat <<EOF_DBAAS_BACKUP_LOG
. {{CONFIG_BACKUP_LOG_SCRIPT}}

TODAY=\`date +%Y_%m_%d\`
TARGET_BACKUP_PATH=\${DST_PATH}/\${TODAY}

if [ ! -d "\${DST_PATH}" ]; then
    echo "Mount NFS is not accessible!"
    exit 1
fi

remove_old_backups()
{
    if [ -d "\${TARGET_BACKUP_PATH}" ]; then
        # This is not the first backup of the day
        return
    fi

    cd \${DST_PATH}
    OLDEST_BACKUP=\`date +"%Y%m%d" --date="\${RETENTION_BACKUP_LOG_DAYS} day ago"\`
    find . -maxdepth 1 -type d -name "20[0-9][0-9]_*" | while read BACKUP_DIR
    do
        BACKUP_DIR_INT=\`echo \${BACKUP_DIR} | cut -c3-12 | sed 's/_//g'\`
        if [ \${OLDEST_BACKUP} -ge \${BACKUP_DIR_INT} ]
        then
            echo "Removing \${BACKUP_DIR}"
            rm -Rf \${BACKUP_DIR}
        fi
    done
}

remove_old_backups

mkdir -p \${TARGET_BACKUP_PATH}
rsync -av --delete-after \${DATABASE_LOG_PATH} \${TARGET_BACKUP_PATH}

EOF_DBAAS_BACKUP_LOG
) > {{BACKUP_LOG_SCRIPT}}
    die_if_error "Error setting {{BACKUP_LOG_SCRIPT}}"

    chmod u+x {{BACKUP_LOG_SCRIPT}}
    die_if_error "Error changing {{BACKUP_LOG_SCRIPT}} permission"

    echo "{{BACKUP_LOG_CRON_MINUTE}} {{BACKUP_LOG_CRON_HOUR}} * * * {{BACKUP_LOG_SCRIPT}} > /tmp/backup_log.txt" >> /var/spool/cron/root
    die_if_error "Error adding backup log script in cron"
}

mountbackuplogdisk
createbackuplogfilescript
    """
