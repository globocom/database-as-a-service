# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import logging

from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework import viewsets
from rest_framework.response import Response
# from rest_framework.decorators import action, link
from rest_framework.decorators import api_view, renderer_classes

from physical.models import Engine, EngineType, DatabaseInfra, Instance
from logical.models import Database, Credential
from tsuru.models import Bind
from drivers import factory_for


LOG = logging.getLogger(__name__)

def __check_service_availability(engine_name, engine_version):
    """
    Checks the availability of the service.
    Returns the engine.
    
    """
    engine = None
    try:
        engine_type = EngineType.objects.get(name=engine_name)
        engine = Engine.objects.get(engine_type=engine_type, version=engine_version)
    except EngineType.DoesNotExist:
        LOG.warning("endpoint not available for %s_%s" % (engine_name, engine_version))
    except Engine.DoesNotExist:
        LOG.warning("endpoint not available for %s_%s" % (engine_name, engine_version))
    
    return engine

@api_view(['GET'])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_status(request, engine_name=None, engine_version=None, service_name=None):
    """
    To check the status of an databaseinfra, tsuru uses the url /resources/<service_name>/status. 
    If the databaseinfra is ok, this URL should return 204.
    """
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    LOG.info("status for service %s" % (service_name))
    try:
        databaseinfra = DatabaseInfra.objects.get(name=service_name)
        factory_for(databaseinfra).check_status()
        return Response(data={"status": "ok"}, status=204)
    except DatabaseInfra.DoesNotExist:
        LOG.warning("databaseinfra not found for service %s" % (service_name))
        return Response(data={"status": "not_found"}, status=404)
    except Exception, e:
        return Response(data={"error": "%s" % e}, status=500)


@api_view(['POST'])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_add(request, engine_name=None, engine_version=None):
    """
    Responds to tsuru's service_add call.
    
    Creates a new databaseinfra.
    
    Return codes:
    201: when the databaseinfra is successfully created. You don’t need to include any content in the response body.
    500: in case of any failure in the creation process. Make sure you include an explanation for the failure in the response body.
    """
    LOG.info("service_add for %s(%s)" % (engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    # LOG.debug("request meta: %s" % request.META)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    service_name = data.get('name', None)
    LOG.info("creating service %s" % (service_name))
    try:
        databaseinfra = DatabaseInfra.provision(engine=engine,name=service_name)
        return Response({"hostname": databaseinfra.instance.address, 
                        "engine_type" : engine.name,
                        "version" : engine.version,
                        "databaseinfra_name" : databaseinfra.name}, 
                        status=201)
    except Exception, e:
        LOG.error("error provisioning databaseinfra %s: %s" % (service_name, e))


@api_view(['POST','DELETE',])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_bind_remove(request, engine_name=None, engine_version=None, service_name=None):
    """
    Service bind and service bind shares the same url structure
    """
    if request.method == "POST":
        return service_bind(request, engine_name=engine_name, engine_version=engine_version, service_name=service_name)
    elif request.method == "DELETE":
        return service_remove(request, engine_name=engine_name, engine_version=engine_version, service_name=service_name)


@api_view(['DELETE'])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_remove(request, engine_name=None, engine_version=None, service_name=None):
    """
    In the destroy action, tsuru calls your service via DELETE on /resources/<service_name>/.

    If the service databaseinfra is successfully removed you should return 200 as status code.
    """
    LOG.info("service_remove for service %s using %s(%s)" % (service_name, engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    # LOG.debug("request meta: %s" % request.META)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA

    LOG.info("removing service %s" % (service_name))
    #removes database
    try:
        database = Database.objects.get(name=service_name)
        database.delete()
    except Database.DoesNotExist:
        LOG.warning("database not found for service %s" % (service_name))
    except Exception, e:
        LOG.error("error removing database %s: %s" % (service_name, e))
        return Response(data={"error": "%s" % e}, status=500)
        
    #removes databaseinfra
    try:
        databaseinfra = DatabaseInfra.objects.get(name=service_name)
        driver = factory_for(databaseinfra)
        databaseinfra.delete()
        return Response(data={"status": "ok"}, status=200)
    except DatabaseInfra.DoesNotExist:
        LOG.warning("databaseinfra not found for service %s" % (service_name))
        return Response(data={"status": "not_found"}, status=404)
    except Exception, e:
        LOG.error("error removing databaseinfra %s: %s" % (service_name, e))
        return Response(data={"error": "%s" % e}, status=500)


@api_view(['POST'])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_bind(request, engine_name=None, engine_version=None, service_name=None):
    """
    In the bind action, tsuru calls your service via POST on /resources/<service_name>/ with the "app-hostname" 
    that represents the app hostname and the "unit-hostname" that represents the unit hostname on body.

    If the app is successfully binded to the databaseinfra, you should return 201 as status code with the variables 
    to be exported in the app environment on body with the json format.
    """
    LOG.info("service_bind for %s > %s(%s)" % (service_name, engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    # print("request meta: %s" % request.META)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    try:
        #get databaseinfra
        databaseinfra = DatabaseInfra.objects.get(name=service_name)
        unit_host = data.get("unit-host", "N/A")
        app_host = data["app-host"]
        #provision database
        with transaction.commit_on_success():
            Bind(service_name=service_name, service_hostname=unit_host, databaseinfra=databaseinfra).save()
            response=databaseinfra.env_variables(database_name=service_name)
            return Response(data=response, 
                            status=201)
    except DatabaseInfra.DoesNotExist:
        LOG.warning("databaseinfra not found for service %s" % (service_name))
        return Response(data={"status": "error", "reason": "databaseinfra %s not found" % service_name}, status=404)


@api_view(['DELETE'])
@renderer_classes((JSONRenderer, JSONPRenderer))
def service_unbind(request, engine_name=None, engine_version=None, service_name=None, host=None):
    """
    In the unbind action, tsuru calls your service via DELETE on /resources/<hostname>/hostname/<unit_hostname>/.

    If the app is successfully unbinded from the databaseinfra you should return 200 as status code.
    """
    LOG.info("service_unbind for %s at %s > %s(%s)" % (service_name, host, engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    try:
        databaseinfra = DatabaseInfra.objects.get(name=service_name)
        database = Database.objects.get(name=service_name)
        with transaction.commit_on_success():
            #removes credentials
            credentials = Credential.objects.filter(database=database, user=Credential.USER_PATTERN % (database.name))
            LOG.info("Credentials registered in dbaas for database %s that will be deleted: %s" % (database.name, credentials))
            [credential.delete() for credential in credentials]
            
            #get binds and delete all
            binds = Bind.objects.filter(service_name=service_name, service_hostname=host, databaseinfra=databaseinfra)
            LOG.info("Binds registered in dbaas that will be deleted: %s" % binds)
            [bind.delete() for bind in binds]
            return Response({"action": "service_unbind"}, 
                            status=200)
    except DatabaseInfra.DoesNotExist:
        LOG.warning("databaseinfra not found for service %s" % (service_name))
        return Response(data={"status": "error", "reason": "databaseinfra %s not found" % service_name}, status=404)
    except Database.DoesNotExist:
        LOG.warning("database %s not found" % (service_name))
        return Response(data={"status": "warning", "reason": "database %s not found" % service_name}, status=200)

