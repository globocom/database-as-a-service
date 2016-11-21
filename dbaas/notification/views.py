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
