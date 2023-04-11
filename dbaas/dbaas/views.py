from system.models import Configuration
from django.views.generic import TemplateView


def external_links(request):
    iaas_status = Configuration.get_by_name('iaas_status')
    iaas_quota = Configuration.get_by_name('iaas_quota')


    return {'iaas_status': iaas_status,
            'iaas_quota': iaas_quota}


class DeployView(TemplateView):
    template_name = 'deploy/deploy.html'
