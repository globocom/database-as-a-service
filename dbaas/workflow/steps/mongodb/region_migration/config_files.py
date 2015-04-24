# -*- coding: utf-8 -*-
import logging
import os
import shutil
from util import full_stack
from util import check_ssh
from util import exec_remote_command
from util import build_context_script
from util import scp_get_file
from util import scp_put_file
from system.models import Configuration
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0019

LOG = logging.getLogger(__name__)


class ConfigFiles(BaseStep):

    def __unicode__(self):
        return "Config files..."

    def do(self, workflow_dict):
        try:
            
            initial_script = '#!/bin/bash\n\ndie_if_error()\n{\n    local err=$?\n    if [ "$err" != "0" ]; then\n        echo "$*"\n        exit $err\n    fi\n}'
            
            region_migration_dir = Configuration.get_by_name('region_migration_dir')
            if not region_migration_dir:
                region_migration_dir = '/tmp'
            
            workflow_dict['region_migration_dir_infra_name'] = "{}/{}".format(region_migration_dir, workflow_dict['databaseinfra'].name)
            
            for index, source_instance in enumerate(workflow_dict['source_instances']):
                
                source_host = source_instance.hostname
                source_cs_host_attr = CS_HostAttr.objects.get(host = source_host)
                
                hostname = source_host.hostname.split('.')[0]
                localpath = "{}/{}".format(workflow_dict['region_migration_dir_infra_name'], hostname)
                os.makedirs(localpath)
                
                LOG.info('Get source host files to {}'.format(localpath))
                
                if not scp_get_file(server = source_host.address,
                                    username = source_cs_host_attr.vm_user,
                                    password = source_cs_host_attr.vm_password,
                                    localpath = "{}/mongodb.key".format(localpath),
                                    remotepath = "/data/mongodb.key"):
                    raise Exception("FTP Error")

                if not scp_get_file(server = source_host.address,
                                    username = source_cs_host_attr.vm_user,
                                    password = source_cs_host_attr.vm_password,
                                    localpath = "{}/mongodb.conf".format(localpath),
                                    remotepath = "/data/mongodb.conf"):
                    raise Exception("FTP Error")

                if not scp_get_file(server = source_host.address,
                                    username = source_cs_host_attr.vm_user,
                                    password = source_cs_host_attr.vm_password,
                                    localpath = "{}/td-agent.conf".format(localpath),
                                    remotepath = "/etc/td-agent/td-agent.conf"):
                    raise Exception("FTP Error")
                
                target_host = source_host.future_host
                LOG.info(target_host)
                target_cs_host_attr = CS_HostAttr.objects.get(host = target_host)
                
                target_instance = source_instance.future_instance
                if target_instance.instance_type == target_instance.MONGODB_ARBITER:
                    LOG.info("Cheking host ssh...")
                    host_ready = check_ssh(server = target_host.address,
                                           username = target_cs_host_attr.vm_user, 
                                           password = target_cs_host_attr.vm_password,
                                           wait = 5, interval = 10)

                    if not host_ready:
                        raise Exception, str("Host %s is not ready..." % host)

                if not scp_put_file(server = target_host.address,
                                    username = target_cs_host_attr.vm_user,
                                    password = target_cs_host_attr.vm_password,
                                    localpath = "{}/mongodb.key".format(localpath),
                                    remotepath = "/data/mongodb.key"):
                    raise Exception("FTP Error")

                if not scp_put_file(server = target_host.address,
                                    username = target_cs_host_attr.vm_user,
                                    password = target_cs_host_attr.vm_password,
                                    localpath = "{}/mongodb.conf".format(localpath),
                                    remotepath = "/data/mongodb.conf"):
                    raise Exception("FTP Error")

                if not scp_put_file(server = target_host.address,
                                    username = target_cs_host_attr.vm_user,
                                    password = target_cs_host_attr.vm_password,
                                    localpath = "{}/td-agent.conf".format(localpath),
                                    remotepath = "/etc/td-agent/td-agent.conf"):
                    raise Exception("FTP Error")
                
                script = initial_script
                script += '\nmkdir /data/data'
                script += '\ndie_if_error "Error creating data dir"'
                
                script += '\nchown mongodb:mongodb /data'
                script += '\ndie_if_error "Error changing datadir permission"'
                script += '\nchown -R mongodb:mongodb /data/*'
                script += '\ndie_if_error "Error changing datadir permission"'

                script += '\nchmod 600 /data/mongodb.key'
                script += '\ndie_if_error "Error changing mongodb key file permission"'

                script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"'
                script += '\n/etc/init.d/mongodb start > /dev/null'
                script += '\ndie_if_error "Error starting database"'
                script = build_context_script({}, script)
                output = {}
                LOG.info(script)
                return_code = exec_remote_command(server=target_host.address,
                                                  username=target_cs_host_attr.vm_user,
                                                  password=target_cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    raise Exception, str(output)

            shutil.rmtree(workflow_dict['region_migration_dir_infra_name'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            
            script = '/etc/init.d/mongodb stop'
            script += '\nrm -rf /data/*'
            script = build_context_script({}, script)
            for target_instance in workflow_dict['target_instances']:
                target_host = target_instance.hostname
                target_cs_host_attr = CS_HostAttr.objects.get(host = target_host)
                output = {}
                exec_remote_command(server = target_host.address,
                                    username = target_cs_host_attr.vm_user,
                                    password = target_cs_host_attr.vm_password,
                                    command = script,
                                    output = output)
                LOG.info(output)

            try:
                if 'region_migration_dir_infra_name' in workflow_dict:
                    shutil.rmtree(workflow_dict['region_migration_dir_infra_name'])
            except Exception:
                pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
