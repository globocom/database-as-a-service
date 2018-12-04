from system.models import Configuration
from django.template import Context
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from physical.models import Environment


def external_links(request):
    iaas_status = Configuration.get_by_name('iaas_status')
    iaas_quota = Configuration.get_by_name('iaas_quota')

    try:
        credential = get_credentials_for(
            environment=Environment.objects.first(),
            credential_type=CredentialType.GRAFANA
        )

        sofia_dashboard = "{}/{}?var-datasource={}".format(
            credential.endpoint,
            credential.get_parameter_by_name('sofia_dbaas_dashboard'),
            credential.get_parameter_by_name('datasource')
        )
    except IndexError:
        sofia_dashboard = ""

    return {'iaas_status': iaas_status,
            'iaas_quota': iaas_quota,
            'sofia_main_dashboard': sofia_dashboard}
