from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
import logging
from logical.models import Database
from physical.models import Plan
from django.utils.html import strip_tags
from rest_framework import status

LOG = logging.getLogger(__name__)

class ListPlans(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Plan

    def get(self, request, format=None):
        """
        Return a list of all plans.
        """

        hard_plans = Plan.objects.values('name', 'description'
            , 'environments__name').extra(where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)])

        plans = []

        for hard_plan in hard_plans:
            hard_plan['name'] = hard_plan['name'] +'-'+ hard_plan['environments__name']
            hard_plan['description'] = strip_tags(hard_plan['description'])
            del hard_plan['environments__name']
            plans.append(hard_plan)

        return Response(plans)

class GetServiceStatus(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database


    def get(self, request, database_id, format=None):

        try:
            database_status = Database.objects.values_list('status', flat=True).extra(where=['id={}'.format(database_id),])[0]
        except IndexError, e:
            database_status=2
            LOG.warn("There is not a database with this {} id. {}".format(database_id,e))

        LOG.info("Status = {}".format(database_status))

        if database_status == Database.ALIVE:
            database_status = status.HTTP_204_NO_CONTENT
        elif database_status == Database.DEAD:
            database_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            database_status = status.HTTP_202_ACCEPTED

        return Response(status=database_status)
