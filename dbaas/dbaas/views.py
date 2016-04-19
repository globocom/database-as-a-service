from system.models import Configuration
from django.template import Context


def external_links(request):
    iaas_status = Configuration.get_by_name('iaas_status')
    iaas_quota = Configuration.get_by_name('iaas_quota')
    return {'iaas_status': iaas_status, 'iaas_quota': iaas_quota }
