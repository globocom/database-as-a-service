from system.models import Configuration
from django.views.generic import TemplateView


def external_links(request):
    iaas_status = Configuration.get_by_name('iaas_status')
    iaas_quota = Configuration.get_by_name('iaas_quota')
    sofia_grafana_url = Configuration.get_by_name('sofia_grafana_url')
    sofia_grafana_datasource = Configuration.get_by_name('sofia_grafana_datasource')
    sofia_dashboard = "{}?var-datasource={}".format(sofia_grafana_url, sofia_grafana_datasource)

    return {'iaas_status': iaas_status,
            'iaas_quota': iaas_quota,
            'sofia_main_dashboard': sofia_dashboard}


class DeployView(TemplateView):
    template_name = 'deploy/deploy.html'
