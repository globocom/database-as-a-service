import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr, Group
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
    return Provider(dbaas_api, HostAttr, Group)


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


def create_access(environment, export_path, host):
    provider = get_faas_provider(environment=environment)
    return provider.create_access(
        export_path=export_path, address=host.address
    )
