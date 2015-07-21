from django.http import HttpResponse
from models import CeleryHealthCheck


def CeleryHealthCheckView(request):
    return HttpResponse(CeleryHealthCheck.get_healthcheck_string())
