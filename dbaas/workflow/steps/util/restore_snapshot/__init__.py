# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from workflow.steps.util.nfsaas_utils import create_snapshot
from util import exec_remote_command

LOG = logging.getLogger(__name__)


def use_database_initialization_script(databaseinfra, host, option):
    driver = databaseinfra.get_driver()
    initialization_script = driver.initialization_script_path(host)

    command = initialization_script.format(option=option)
    command += ' > /dev/null'

    cs_host_attr = CsHostAttr.objects.get(host=host)

    output = {}
    return_code = exec_remote_command(server=host.address,
                                      username=cs_host_attr.vm_user,
                                      password=cs_host_attr.vm_password,
                                      command=command,
                                      output=output)

    return return_code, output


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


def make_host_backup(database, instance, export_id):
    from backup.models import Snapshot
    from dbaas_nfsaas.models import HostAttr as Disk
    import datetime

    LOG.info("Make instance backup for %s" % (instance))

    disk = Disk.objects.get(nfsaas_export_id=export_id)
    databaseinfra = instance.databaseinfra

    snapshot = Snapshot()
    snapshot.start_at = datetime.datetime.now()
    snapshot.type = Snapshot.SNAPSHOPT
    snapshot.status = Snapshot.RUNNING
    snapshot.instance = instance
    snapshot.environment = databaseinfra.environment
    snapshot.export_path = disk.nfsaas_path
    snapshot.database_name = database.name

    nfs_snapshot = create_snapshot(
        environment=databaseinfra.environment, host=instance.hostname
    )

    if 'id' in nfs_snapshot and 'name' in nfs_snapshot:
        snapshot.status = Snapshot.SUCCESS
        snapshot.snapshopt_id = nfs_snapshot['id']
        snapshot.snapshot_name = nfs_snapshot['name']
        snapshot.end_at = datetime.datetime.now()
        snapshot.save()
        return True
    else:
        snapshot.status = Snapshot.ERROR
        snapshot.end_at = datetime.datetime.now()
        snapshot.save()
        return False
