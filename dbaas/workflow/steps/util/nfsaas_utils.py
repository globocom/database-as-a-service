import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from dbaas_nfsaas.dbaas_api import DatabaseAsAServiceApi
from dbaas_nfsaas.faas_provider import Provider
from util import get_credentials_for

LOG = logging.getLogger(__name__)


def get_faas_provider(environment):

    faas_credentials = get_credentials_for(
        environment=environment,
        credential_type=CredentialType.FAAS
    )
    dbaas_api = DatabaseAsAServiceApi(credentials=faas_credentials)
    return Provider(dbaas_api, HostAttr)


def create_disk(enviroment, host, plan):
    provider = get_faas_provider(environment=enviroment)

    LOG.info("Creating NFS disk...")
    disk = provider.create_export(
        host=host, size_kb=plan.disk_offering.size_kb
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
    disk = HostAttr.objects.get(host=host)
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
