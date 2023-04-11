from system.models import Configuration
from django.views.generic import TemplateView
from account.models import Role


def external_links(request):
    iaas_status = Configuration.get_by_name('iaas_status')
    iaas_quota = Configuration.get_by_name('iaas_quota')

    user = str(request.user)
    role_dba = Role.objects.get(name='role_dba')
    users_if_dba_role = role_dba.team_set.values_list('name', flat=True)

    if user in users_if_dba_role:
        is_dba = True
    else:
        is_dba = False

    return {'iaas_status': iaas_status,
            'iaas_quota': iaas_quota,
            'is_dba': is_dba}


class DeployView(TemplateView):
    template_name = 'deploy/deploy.html'


