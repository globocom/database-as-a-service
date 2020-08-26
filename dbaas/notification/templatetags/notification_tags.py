# coding: utf-8
import re
from django import template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from notification.views import UserTasks


register = template.Library()
ARGUMENTS_REGEX = re.compile(r"database( name)?: ([\w\-_\ ]+),?", re.IGNORECASE)


@register.simple_tag
def get_notifications(username):

    def get_css_class(task_status):
        if task_status == "RUNNING":
            return "warning"
        if task_status == "WAITING":
            return "inverse"
        if task_status == "ERROR":
            return "important"
        if task_status:
            return task_status.lower()

    def parse_arguments(arguments):
        result = re.search(ARGUMENTS_REGEX, arguments)
        try:
            return result.group(2) if result else 'not found'
        except IndexError:
            return 'not found'

    notification_menu_tmpl = '''
        <a class="dropdown-toggle uni" id="dLabel" role="button" data-toggle="dropdown" data-target="#" href="#">
            <span class="badge badge-{} notification-cnt">{}</span>
            <span class="text-{} notify-text">Notifications
            <i class="fa fa-bell text-{}"></i></span>
        </a>
        <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel" >
            {}
        </ul>
    '''
    li_tmpl = '''
        <li class="{li_class}" data-task-id="{task_id}" data-task-status="{task_status}" data-is-new="{is_new}">
            <a href="{url}?id={task_id}" class="notify-info" id="teste">
                <span class="notify-label"><span class="label label-{task_status_css_class}">{task_status}</span></span>
                <span class="notify-body">
                    <div class="notify-task"><span class="notify-description">task name:</span> {parsed_task_name}</div>
                    <div class="notify-database"><b>database:</b> {parsed_arguments}</div>
                </span>
                <span class="notify-new"><i class="icon-eye-open"></i></span>
            </a>
        </li>'''

    tasks = UserTasks.get_notifications(username)
    lis_html = ''
    notification_count = 0
    for task in tasks:
        task.update({
            'li_class': '' if int(task.get('read')) else 'new',
            'task_status_css_class': get_css_class(task.get('task_status')),
            'parsed_task_name': task['task_name'].split('.')[-1],
            'parsed_arguments': task.get('database_name') or parse_arguments(task['arguments']),
            'url': reverse('admin:notification_taskhistory_changelist')
        })
        lis_html += li_tmpl.format(**task)
        if int(task['is_new']):
            notification_count += 1
    if not tasks:
        lis_html = '<li class="no-notification">No tasks found.</li>'
    return mark_safe(notification_menu_tmpl.format(
        'warning' if notification_count else 'default',
        notification_count,
        'warning' if notification_count else 'default',
        'warning' if notification_count else 'white',
        lis_html)
    )
