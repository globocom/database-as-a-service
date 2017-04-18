# -*- coding: utf-8 -*-
from json import dumps
from django.http import HttpResponse
from models import TaskHistory


def running_tasks_api(self):
    tasks = TaskHistory.running_tasks()
    response_json = dumps({
        task.id: task.task_name for task in tasks
    })
    return HttpResponse(response_json, content_type="application/json")


def waiting_tasks_api(self):
    tasks = TaskHistory.waiting_tasks()
    response_json = dumps({
        task.id: task.task_name for task in tasks
    })
    return HttpResponse(response_json, content_type="application/json")


def database_tasks(self, database_id):
    task = TaskHistory.objects.filter(lock__database__id=database_id).first()

    response = {}
    if task:
        name = task.task_name.split('.')[-1]
        name = name.replace("_", " ")

        step = task.details.split('\n')[-1]
        if "Step" in step:
            step = step.split(" - ", 1)[1]

        response = {
            'id': task.id,
            'name': name.capitalize(),
            'status': task.task_status.capitalize(),
            'step': step
        }

    return HttpResponse(dumps(response), content_type="application/json")
