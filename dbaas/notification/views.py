# -*- coding: utf-8 -*-
import json
from json import dumps
from django.http import HttpResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from models import TaskHistory
from django_redis import get_redis_connection


class JSONResponseMixin(object):
    '''
    A mixin that can be used to render a JSON response
    '''
    response_class = HttpResponse

    def render_to_response(self, context, **response_kwargs):
        '''
        Returns a JSON response, transforming 'context' to make the payload
        '''
        response_kwargs['content_type'] = 'application/json'
        return self.response_class(
            self.convert_context_to_json(context),
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        'Convert the context dictionary into a JSON object'
        # Note: You may garantee that all context are json serializable
        return json.dumps(context)


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

        step = task.details.split('\n')[-1] if task.details else ''
        if "Step" in step:
            step = step.split(" - ", 1)[1]

        response = {
            'id': task.id,
            'name': name.capitalize(),
            'status': task.task_status.capitalize(),
            'step': step
        }

    return HttpResponse(dumps(response), content_type="application/json")


class UserTasks(View, JSONResponseMixin):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(UserTasks, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get_notifications(username):
        if username:
            conn = get_redis_connection('notification')
            keys = conn.keys("task_users:{}:*".format(username))
            # TODO: can be better
            tasks = map(conn.hgetall, keys) if keys else []
            return sorted(tasks, key=lambda d: d['updated_at'], reverse=True)
        return []

    def get(self, *args, **kw):
        username = kw.get('username')
        context = self.get_notifications(username)
        return self.render_to_response(context)

    def post(self, *args, **kw):
        username = kw.get('username')
        conn = get_redis_connection('notification')
        payload = json.loads(self.request.body)
        for task in payload.get('ids', []):
            key = "task_users:{}:{}".format(username, task['id'])
            # TODO: Do all logic use fields
            fields = task.get('fields')
            if fields:
                for field in fields:
                    field_key = field.keys()[0]
                    conn.hset(key, field_key, field[field_key])
            else:
                task_status = conn.hget(key, 'task_status')
                if task_status == task['status']:
                    conn.hset(key, 'is_new', 0)

        return self.render_to_response('ok')
