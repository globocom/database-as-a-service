# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging

from rest_framework import viewsets
from rest_framework.response import Response
# from rest_framework.decorators import action, link
from rest_framework.decorators import api_view

from physical.models import Engine, EngineType, Instance, Node
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
def status(request, engine_name=None, engine_version=None, service_name=None):
    """
    To check the status of an instance, tsuru uses the url /resources/<service_name>/status. 
    If the instance is ok, this URL should return 204.
    """
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    LOG.info("status for service %s" % (service_name))
    try:
        instance = Instance.objects.get(name=service_name)
        factory_for(instance).check_status()
        return Response(data={"status": "ok"}, status=204)
    except Instance.DoesNotExist:
        LOG.warning("instance not found for service %s" % (service_name))
        return Response(data={"status": "not_found"}, status=404)
    except Exception, e:
        return Response(data={"error": "%s" % e}, status=500)

        
@api_view(['POST'])
def service_add(request, engine_name=None, engine_version=None):
    """
    Responds to tsuru's service_add call.
    
    Creates a new instance.
    
    Return codes:
    201: when the instance is successfully created. You don’t need to include any content in the response body.
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
        instance = Instance.provision(engine=engine,name=service_name)
        return Response({"hostname": instance.node.address, 
                        "engine_type" : engine.engine_type.name,
                        "version" : engine.version,
                        "instance_name" : instance.name}, 
                        status=201)
    except Exception, e:
        LOG.error("error provisioning instance %s: %s" % (service_name, e))

@api_view(['POST'])
def service_bind(request, engine_name=None, engine_version=None, service_name=None):
    """
    In the bind action, tsuru calls your service via POST on /resources/<service_name>/ with the "app-hostname" 
    that represents the app hostname and the "unit-hostname" that represents the unit hostname on body.

    If the app is successfully binded to the instance, you should return 201 as status code with the variables 
    to be exported in the app environment on body with the json format.
    """
    LOG.info("service_bind for %s > %s(%s)" % (service_name, engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    print "*" * 50
    print("request meta: %s" % request.META)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    
    return Response({"action": "service_bind"}, 
                    status=201)


@api_view(['DELETE'])
def service_unbind(request, engine_name=None, engine_version=None, service_name=None, host=None):
    """
    In the unbind action, tsuru calls your service via DELETE on /resources/<hostname>/hostname/<unit_hostname>/.

    If the app is successfully unbinded from the instance you should return 200 as status code.
    """
    LOG.info("service_unbind for %s at %s > %s(%s)" % (service_name, host, engine_name, engine_version))
    
    LOG.debug("request DATA: %s" % request.DATA)
    LOG.debug("request QUERY_PARAMS: %s" % request.QUERY_PARAMS)
    LOG.debug("request content-type: %s" % request.content_type)
    #print("request meta: %s" % request.META)
    engine = __check_service_availability(engine_name, engine_version)
    if not engine:
        return Response(data={"error": "endpoint not available for %s(%s)" % (engine_name, engine_version)}, status=500)
    
    data = request.DATA
    
    return Response({"action": "service_unbind"}, 
                    status=200)
