# -*- coding: utf-8 -*-
import logging
from datetime import date
from dbaas.celery import app
from account.models import Team
from util import get_worker_name
from logical.models import Database
from util import email_notifications
from util.decorators import only_one
from notification.models import TaskHistory
from dbaas_services.analyzing.models import AnalyzeRepository


LOG = logging.getLogger(__name__)


@app.task(bind=True)
@only_one(key="analyzing_notification_key", timeout=180)
def database_notification(self):
    LOG.info("retrieving all teams and sending database notification")
    teams = Team.objects.all()
    msgs = {}

    for team in teams:
        ###############################################
        # create task
        ###############################################

        msgs[team] = analyzing_notification_for_team(team=team)
        ###############################################

    try:
        LOG.info("Messages: ")
        LOG.info(msgs)

        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details="\n".join(
            str(key) + ': ' + ', '.join(value) for key, value in msgs.items()))
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

    return


def analyzing_notification_for_team(team=None):
    LOG.info("sending database notification for team %s" % team)

    databases = Database.objects.filter(team=team, is_in_quarantine=False)
    msgs = []
    for database in databases:
        analyzing_repositories = AnalyzeRepository.objects.filter(analyzed_at__startswith=date.today(),
                                                                  database_name=database.name,
                                                                  databaseinfra_name=database.databaseinfra.name).values('volume_alarm',
                                                                                                                         'cpu_alarm',
                                                                                                                         'memory_alarm',
                                                                                                                         'cpu_threshold',
                                                                                                                         'memory_threshold',
                                                                                                                         'volume_threshold').annotate()
        if not analyzing_repositories:
            continue
        else:
            analyzing_repositories = analyzing_repositories[0]

        msg = 'used less than {}% of {}'
        sub_msg = []
        if analyzing_repositories['memory_alarm']:
            threshold = analyzing_repositories['memory_threshold']
            m_msg = msg.format(threshold, 'memory')
            sub_msg.append(m_msg)
        if analyzing_repositories['cpu_alarm']:
            threshold = analyzing_repositories['cpu_threshold']
            c_msg = msg.format(threshold, 'cpu')
            sub_msg.append(c_msg)
        if analyzing_repositories['volume_alarm']:
            threshold = analyzing_repositories['volume_threshold']
            v_msg = msg.format(threshold, 'volume')
            sub_msg.append(v_msg)

        msg = ", ".join(sub_msg)
        LOG.info(msg)
        msgs.append(msg)

        LOG.info("Sending database notification...")
        context = {}
        context['database'] = database.name
        context['team'] = team
        context['msg'] = msg
        context['environment'] = database.environment.name
        email_notifications.database_analyzing(context=context)

    return msgs
