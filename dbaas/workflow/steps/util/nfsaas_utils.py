import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from dbaas_nfsaas.dbaas_api import DatabaseAsAServiceApi
from dbaas_nfsaas.faas_provider import Provider
from dbaas_nfsaas.util import delete_all_disk_files
from util import get_credentials_for

LOG = logging.getLogger(__name__)


def get_faas_provider(environment):

    faas_credentials = get_credentials_for(
        environment=environment,
        credential_type=CredentialType.FAAS
    )
    dbaas_api = DatabaseAsAServiceApi(credentials=faas_credentials)
    return Provider(dbaas_api, HostAttr)


def create_disk(environment, host, size_kb):
    provider = get_faas_provider(environment=environment)

    LOG.info("Creating NFS disk...")
    disk = provider.create_export(
        host=host, size_kb=size_kb
    )

    LOG.info(
        "Creating NFS access to disk: {}".format(disk.nfsaas_path_host)
    )
    provider.create_access(
        export_path=disk.nfsaas_path_host, address=host.address
    )

    return disk


def delete_disk(environment, host):
    provider = get_faas_provider(environment=environment)

    LOG.info("Destroying NFS export...")
    for disk in HostAttr.objects.filter(host=host):
        if not provider.delete_export(path=disk.nfsaas_path_host):
            return False
    return True


def delete_export(environment, export_path):
    provider = get_faas_provider(environment=environment)
    return provider.delete_export(path=export_path)


def create_snapshot(environment, host):
    provider = get_faas_provider(environment=environment)
    disk = HostAttr.objects.get(host=host, is_active=True)
    result = provider.create_snapshot(export_path=disk.nfsaas_path_host)
    return result['snapshot']


def delete_snapshot(snapshot):
    provider = get_faas_provider(
        environment=snapshot.instance.databaseinfra.environment
    )
    disk = HostAttr.objects.get(nfsaas_path=snapshot.export_path)
    return provider.delete_snapshot(
        export_path=disk.nfsaas_path_host, snapshot_id=snapshot.snapshopt_id
    )


def restore_snapshot(environment, export_id, snapshot_id):
    provider = get_faas_provider(environment=environment)
    disk = HostAttr.objects.get(nfsaas_export_id=export_id)

    return provider.restore_snapshot(
        export_path=disk.nfsaas_path_host, snapshot_id=snapshot_id
    )


def restore_wait_for_finished(environment, job_id):
    provider = get_faas_provider(environment=environment)
    return provider.wait_for_job_finished(restore_job=job_id)


def create_access(environment, export_path, host):
    provider = get_faas_provider(environment=environment)
    return provider.create_access(
        export_path=export_path, address=host.address
    )


def delete_access(environment, export_id, host_delete):
    provider = get_faas_provider(environment=environment)
    disk = HostAttr.objects.get(nfsaas_export_id=export_id)

    accesses = provider.list_access(disk.nfsaas_path_host)
    if not accesses:
        return True

    for access in accesses:
        if access['host'] == host_delete.address:
            return provider.delete_access(
                disk.nfsaas_path_host, host_delete.address
            )

    return False


def clean_unused_data(export_id):
    disk = HostAttr.objects.get(nfsaas_export_id=export_id)

    delete_all_disk_files(
        disk.nfsaas_path, disk.nfsaas_path_host,
        disk.nfsaas_export_id, disk.host
    )


def resize_disk(environment, host, disk_offering):
    provider = get_faas_provider(environment=environment)
    for disk in HostAttr.objects.filter(host=host):
        if not provider.resize(disk.nfsaas_path_host, disk_offering.size_kb):
            return False

        disk.nfsaas_size_kb = disk_offering.size_kb
        disk.save()
    return True
