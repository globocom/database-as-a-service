# -*- coding: utf-8 -*-
from django import template

from physical.models import EngineType, Environment, Plan

register = template.Library()


@register.inclusion_tag('dashboard/menu.html')
def render_menu():

    data_engines = []
    for engine_type in EngineType.objects.all():
        data_engine = {
            'name': engine_type.name,
            'environments': [],
        }

        for environment in Environment.objects.filter(plan__in=Plan.objects.filter(engine__engine_type=engine_type)).distinct():
            data_environment = {
                'id': environment.id,
                'name': environment.name,
            }
            data_engine['environments'].append(data_environment)

        if data_engine['environments']:
            data_engines.append(data_engine)

    context = {
        'engines': data_engines
    }

    return context
