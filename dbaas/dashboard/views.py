import logging
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from physical.models import DatabaseInfra
from logical.models import Database
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from physical.models import Environment

LOG = logging.getLogger(__name__)


@login_required
def dashboard(request):
    env_id = request.GET.get('env_id')
    engine_type = request.GET.get('engine_type')
    dbinfra_list = DatabaseInfra.objects.all().order_by('name')
    url_par = "?"
    if env_id or engine_type:
        if env_id:
            url_par += "env_id=" + str(env_id) + "&"
            dbinfra_list = dbinfra_list.filter(environment__id=env_id)
        if engine_type:
            url_par += "engine_type=" + str(engine_type) + "&"
            dbinfra_list = dbinfra_list.filter(engine__engine_type__name=engine_type)

    paginator = Paginator(dbinfra_list,100)

    try:
        page = int(request.GET.get('page','1'))
    except:
        page = 1

    try:
        dbinfra = paginator.page(page)

    except(EmptyPage, InvalidPage):
        dbinfra = paginator.page(paginator.num_pages)
    return render_to_response("dashboard/dashboard.html", {'dbinfra': dbinfra, 'url_par': url_par}, context_instance=RequestContext(request))


@login_required
def databaseinfra(request, infra_id):
    dbinfra = DatabaseInfra.objects.get(pk=infra_id)
    databases = Database.objects.filter(databaseinfra=dbinfra)
    return render_to_response("dashboard/databaseinfra.html", {'infra': dbinfra, 'databases': databases}, context_instance=RequestContext(request))


@login_required
def sofia_dashboard(request):

    credential = get_credentials_for(
        environment=Environment.objects.first(),
        credential_type=CredentialType.GRAFANA
    )

    sofia_dashboard = "{}/{}?var-datasource={}".format(
        credential.endpoint,
        credential.get_parameter_by_name('sofia_dbaas_dashboard'),
        credential.get_parameter_by_name('datasource')
        )

    return render_to_response("dashboard/sofia_dashboard.html", {'sofia_dashboard':sofia_dashboard}, context_instance=RequestContext(request))
