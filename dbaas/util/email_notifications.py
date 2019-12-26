# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from email_extras.utils import send_mail_template
from system.models import Configuration

LOG = logging.getLogger(__name__)


def get_domain():
    domain = Site.objects.get(id=1).domain
    if not domain.startswith('http'):
        return "http://" + domain

    return domain


def email_from():
    return Configuration.get_by_name("email_addr_from")


def email_to(team):
    if team and team.email:
        return [team.email, Configuration.get_by_name("new_user_notify_email")]
    return Configuration.get_by_name("new_user_notify_email")


def get_database_url(uuid):
    return get_domain() + reverse('admin:logical_database_hosts',
                                  kwargs={'id': uuid})


def notify_new_user_creation(user=None):
    subject = _("[DBAAS] a new user has just been created: %s" % user.username)
    template = "new_user_notification"
    addr_from = Configuration.get_by_name("email_addr_from")
    addr_to = Configuration.get_by_name_as_list("new_user_notify_email")
    context = {}
    context['user'] = user
    domain = get_domain()
    context['url'] = domain + reverse('admin:account_team_changelist')
    LOG.debug("user: %s | addr_from: %s | addr_to: %s" %
              (user, addr_from, addr_to))
    if user and addr_from and addr_to:
        send_mail_template(
            subject, template, addr_from, addr_to,
            fail_silently=False, attachments=None, context=context
        )
    else:
        LOG.warning("could not send email for new user creation")


def notify_team_change_for(user=None):
    LOG.info("Notifying team change for user %s" % user)
    subject = _("[DBAAS] your team has been updated!")
    template = "team_change_notification"
    addr_from = Configuration.get_by_name("email_addr_from")
    if user.email:
        addr_to = [user.email]
        context = {}
        context['user'] = user
        domain = get_domain()
        context['url'] = domain
        context['teams'] = [team.name for team in user.team_set.all()]
        if user and addr_from and addr_to:
            send_mail_template(
                subject, template, addr_from, addr_to,
                fail_silently=False, attachments=None, context=context
            )
        else:
            LOG.warning("could not send email for team change")
    else:
        LOG.warning(
            "user %s has no email set and therefore cannot be notified!")


def databaseinfra_ending(context={}):
    LOG.info("Notifying DatabaseInfra ending with context %s" % context)
    subject = _("[DBAAS] DatabaseInfra is almost full")
    template = "infra_notification"
    addr_from = Configuration.get_by_name("email_addr_from")
    addr_to = Configuration.get_by_name_as_list("new_user_notify_email")

    context['domain'] = get_domain()

    send_mail_template(subject, template, addr_from, addr_to,
                       fail_silently=False, attachments=None, context=context)


def database_usage(context={}):
    LOG.info("Notifying Database usage with context %s" % context)
    subject = _("[DBAAS] Database is almost full")
    template = "database_notification"
    addr_from = Configuration.get_by_name("email_addr_from")
    team = context.get("team")
    if team and team.email:
        addr_to = [
            team.email, Configuration.get_by_name("new_user_notify_email")]
    else:
        addr_to = Configuration.get_by_name("new_user_notify_email")

    context['domain'] = get_domain()
    database = context['database']
    context['database_url'] = get_database_url(database.id)

    send_mail_template(subject, template, addr_from, addr_to,
                       fail_silently=False, attachments=None, context=context)


def database_analyzing(context={}):
    LOG.info("Notifying Database alayzing with context %s" % context)
    subject = _("[DBAAS] Database overestimated")
    template = "analyzing_notification"
    addr_from = Configuration.get_by_name("email_addr_from")
    send_email = Configuration.get_by_name("send_analysis_email")
    team = context.get("team")
    if team and team.email and send_email:
        addr_to = [
            team.email, Configuration.get_by_name("new_user_notify_email")]
    else:
        addr_to = Configuration.get_by_name("new_user_notify_email")

    context['domain'] = get_domain()

    send_mail_template(subject, template, addr_from, addr_to,
                       fail_silently=False, attachments=None, context=context)


def disk_resize_notification(database, new_disk, usage_percentage):
    LOG.info(
        'Notifying disk resize {} - {}'.format(database, new_disk)
    )

    subject = _('[DBaaS] Database {} auto disk resize to {}')
    if new_disk.is_last_auto_resize_offering:
        subject = _('[DBaaS] Database {} final auto disk resize to {}')
    subject = subject.format(database.name, new_disk)

    template = "disk_auto_resize_notification"

    context = {
        'domain': get_domain(),
        'database': database,
        'usage_percentage': usage_percentage,
        'new_disk_offering': new_disk,
        'database_url': get_database_url(database.id)
    }

    send_mail_template(
        subject, template, email_from(), email_to(database.team),
        fail_silently=False, attachments=None, context=context
    )


def schedule_task_notification(database, scheduled_task, is_new):

    subject = _('[DBaaS] Automatic Task {} for Database {}'.format(
        'created' if is_new else 'updated',
        database.name,
    ))

    template = "schedule_task_notification"
    domain = get_domain()

    context = {
        'database': database,
        'ssl_expire_at': database.infra.earliest_ssl_expire_at,
        'scheduled_for': scheduled_task.scheduled_for,
        'database_url': "{}{}".format(domain, reverse(
            'admin:logical_database_maintenance', kwargs={'id': database.id}
        )),
        'is_new': is_new,
        'domain': domain
    }

    send_mail_template(
        subject, template, email_from(), email_to(database.team),
        fail_silently=False, attachments=None, context=context
    )
