# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from dbaas_nfsaas.provider import NfsaasProvider
from util import exec_remote_command

LOG = logging.getLogger(__name__)


def use_database_initialization_script(databaseinfra, host, option):
    driver = databaseinfra.get_driver()
    initialization_script = driver.initialization_script_path()

    command = initialization_script + ' ' + option + ' > /dev/null'

    cs_host_attr = CsHostAttr.objects.get(host=host)

    output = {}
    return_code = exec_remote_command(server=host.address,
                                      username=cs_host_attr.vm_user,
                                      password=cs_host_attr.vm_password,
                                      command=command,
                                      output=output)

    return return_code, output


def destroy_unused_export(export_id, export_path, host, databaseinfra):
    provider = NfsaasProvider()
    provider.grant_access(environment=databaseinfra.environment,
                          plan=databaseinfra.plan,
                          host=host,
                          export_id=export_id)

    mount_path = "/mnt_{}_{}".format(databaseinfra.name, export_id)
    command = "mkdir -p {}".format(mount_path)
    command += "\nmount -t nfs -o bg,intr {} {}".format(export_path, mount_path)
    command += "\nrm -rf {}/*".format(mount_path)
    command += "\numount {}".format(mount_path)
    command += "\nrm -rf {}".format(mount_path)
    LOG.info(command)

    cs_host_attr = CsHostAttr.objects.get(host=host)

    output = {}
    exec_remote_command(server=host.address,
                        username=cs_host_attr.vm_user,
                        password=cs_host_attr.vm_password,
                        command=command,
                        output=output)

    LOG.info(output)
    provider.drop_export(environment=databaseinfra.environment,
                         plan=databaseinfra.plan,
                         export_id=export_id)


def update_fstab(host, source_export_path, target_export_path):

    cs_host_attr = CsHostAttr.objects.get(host=host)

    command = """sed -i s/"{}"/"{}"/g /etc/fstab""".format(source_export_path,
                                                           target_export_path)
    output = {}
    return_code = exec_remote_command(server=host.address,
                                      username=cs_host_attr.vm_user,
                                      password=cs_host_attr.vm_password,
                                      command=command,
                                      output=output)
    return return_code, output
