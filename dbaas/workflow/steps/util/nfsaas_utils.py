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
    provider = get_faas_provider(enviroment)

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
    provider = get_faas_provider(environment)

    LOG.info("Destroying NFS export...")
    for disk in HostAttr.objects.filter(host=host):
        if not provider.delete_export(disk.nfsaas_path_host):
            return False
    return True
