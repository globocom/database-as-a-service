from logging import getLogger
from workflow.steps.util.ssl import InfraSSLBaseName

LOG = getLogger(__name__)

script_mongodb_rotate = """cat <<EOT > /opt/dbaas/scripts/mongodb_rotate_script.sh
#!/bin/bash
source /root/.profile
HOST_ADDRESS=\`/bin/hostname -i\`
if [ \$? -ne 0 ]
then
    echo "Host Address not found!"
    exit 3
fi
IS_MASTER=\$(/usr/local/mongodb/bin/mongo \${HOST_ADDRESS}:27017/admin %s --quiet << EOF
db.isMaster()['ismaster']
exit
EOF
)
IS_SECONDARY=\$(/usr/local/mongodb/bin/mongo \${HOST_ADDRESS}:27017/admin %s --quiet << EOF
db.isMaster()['secondary']
exit
EOF
)
# Checking whether node is primary/sencondary or arbiter
if [ "\${IS_MASTER}" = "true" ] || [ "\${IS_SECONDARY}" = "true" ]
then
    /usr/local/mongodb/bin/mongo \$HOST_ADDRESS:27017/admin -u \${MONGODB_ADMIN_USER} -p \${MONGODB_ADMIN_PASSWORD} %s << EOF
    db.runCommand("logRotate");
    exit
EOF
else
    /sbin/pidof mongod | xargs kill -SIGUSR1
fi
# Compress log files already rotated
counter=0
has_compressed_files=0
while [ \$counter -le 5 ] && [ \$has_compressed_files -eq 0 ]
do
  if [[ \$(find /data/logs/ -name 'mongodb.log.*[[:digit:]]' -type f)  ]]
  then
      find /data/logs/ -name 'mongodb.log.*[[:digit:]]' -type f | xargs /usr/bin/gzip -f
      has_compressed_files=1
  else
     (( counter++ ))
     sleep 5
  fi
done
# Remove log backups onder than 7 days
find /data/logs/ -name 'mongodb.log.*.gz' -mtime +7 -type f | xargs rm -f
EOT
"""

script_mongodb_log_params = """cat <<EOT >> /opt/dbaas/scripts/log_rotate_params.sh
#!/bin/bash
(cat <<EOF
export MONGODB_ADMIN_USER=\${MONGODB_ADMIN_USER}
export MONGODB_ADMIN_PASSWORD=\${MONGODB_ADMIN_PASSWORD}
EOF
) >  /root/.profile
"""

script_is_syslog = 'grep syslog /data/mongodb.conf'
script_is_datalog_empty = '[ ! -s /data/logs/mongodb.log ]'
script_rotate_already_executed = '[[ -f /opt/dbaas/scripts/mongodb_rotate_script.sh ]] && [[ -f /opt/dbaas/scripts/log_rotate_params.sh ]]'
remove_log_rotate_file = 'rm -f /etc/logrotate.d/mongodb_rotate'

create_mongodb_rotate_script = 'install -m 755 /dev/null /opt/dbaas/scripts/mongodb_rotate_script.sh'
create_log_params_script = 'install -m 755 /dev/null /opt/dbaas/scripts/log_rotate_params.sh'

create_profile_file = 'export MONGODB_ADMIN_USER={};export MONGODB_ADMIN_PASSWORD={};source /opt/dbaas/scripts/log_rotate_params.sh'
add_cron_job = '! (crontab -l | grep -q "/opt/dbaas/scripts/mongodb_rotate_script.sh") && (crontab -l; echo "0 0 * * * /opt/dbaas/scripts/mongodb_rotate_script.sh") | crontab -'

def execute(task, mongodb_restarted_hosts):
    task.update_details(
        "Checking restarted instances and executing script...", persist=True
    )

    user = password = None
    if mongodb_restarted_hosts:
        first_host = mongodb_restarted_hosts[0]
        instance = first_host.instances.first()
        infra = instance.databaseinfra
        master_ssl_ca = InfraSSLBaseName(instance).master_ssl_ca
        driver = infra.get_driver()
        user, password, _ = driver.build_new_infra_auth()

        if not user or not password:
            raise Exception("Credentials not found")


    for i, host in enumerate(mongodb_restarted_hosts):
        log = '\n{} of {} - Host {}'.format(
            i+1, len(mongodb_restarted_hosts), host
        )
        LOG.info(log)
        task.update_details(log, persist=True)

        infra = host.instances.first().databaseinfra
        if infra.ssl_mode == infra.REQUIRETLS:
            ssl_connect = '--tls --tlsCAFile {}'.format(master_ssl_ca)
        else:
            ssl_connect = ''

        script_mongodb_rotate_formated = script_mongodb_rotate % (
            ssl_connect, ssl_connect, ssl_connect
            )
        output = host.ssh.run_script(
            script=script_is_syslog,
            raise_if_error=False
        )
        if output['exit_code'] == 0:
            msg = '\nHost {}: SYSLOG'.format(host)
            LOG.info(msg)
            task.update_details(msg, persist=True)
        else:
            output = host.ssh.run_script(
                script=script_is_datalog_empty,
                raise_if_error=False
            )
            if output['exit_code'] == 0:
                msg = '\nHost {}: Writing to filer, but it needs restart.'.format(host)
                LOG.info(msg)
                task.update_details(msg, persist=True)
            else:
                output = host.ssh.run_script(
                    script=script_rotate_already_executed,
                    raise_if_error=False
                )
                if output['exit_code'] == 0:
                    msg = '\nHost {}: Rotate already updated.'.format(host)
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                else:
                    msg = '\nStarting log rotate changes.'
                    LOG.info(msg)
                    task.update_details(msg, persist=True)

                    msg = '\nRemoving old rotate file.'
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                    host.ssh.run_script(remove_log_rotate_file)

                    msg = '\nCreating new rotate scripts.'
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                    host.ssh.run_script(create_mongodb_rotate_script)
                    host.ssh.run_script(create_log_params_script)
                    host.ssh.run_script(script_mongodb_rotate_formated)
                    host.ssh.run_script(script_mongodb_log_params)

                    msg = '\nCreating profile file.'
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                    host.ssh.run_script(
                        create_profile_file.format(
                            user, password
                        )
                    )

                    msg = '\nCreating cron job.'
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                    host.ssh.run_script(add_cron_job)

                    msg = '\nHost {}: Rotate script successfully updated.'.format(host)
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
