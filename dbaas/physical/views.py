# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from physical.models import Environment, Engine


def engines_by_env(self, environment_id):
    environment = Environment.objects.get(id=environment_id)
    plans = environment.active_plans()

    engines = []
    for plan in plans:
        if plan.engine.id not in engines:
            engines.append(plan.engine.id)

    response_json = json.dumps({
        "engines": engines
    })
    return HttpResponse(response_json, content_type="application/json")


def plans_details(self):
    context = {
        "environments" : Environment.objects.all(),
        "engines": Engine.objects.all(),
    }
    return render_to_response(
        "plans/plans_details.html",
        context
    )
