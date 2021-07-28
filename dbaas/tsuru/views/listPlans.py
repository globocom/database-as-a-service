from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from physical.models import Plan, Environment
from utils import (get_plans_dict, get_url_env, validate_environment)


class ListPlans(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Plan

    def get(self, request, format=None):
        ''' list all plans in the same
            stage that environment
        '''

        if not validate_environment(request):
            response("Invalid environment", status=403)

        stage = Environment.DEV if\
            get_url_env(request) in Environment.dev_envs() else\
            Environment.PROD

        hard_plans = Plan.objects.filter(
            environments__stage=stage,
            is_active=True,
            environments__tsuru_deploy=True
        ).values(
            'name', 'description',
            'environments__name', 'environments__location_description'
        )
        return Response(get_plans_dict(hard_plans))
