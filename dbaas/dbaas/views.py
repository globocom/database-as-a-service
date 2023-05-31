from django.views.generic import TemplateView


class DeployView(TemplateView):
    template_name = 'deploy/deploy.html'
