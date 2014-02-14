# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from email_extras.utils import send_mail, send_mail_template
from system.models import Configuration

LOG = logging.getLogger(__name__)

def get_domain():
    domain = Site.objects.get(id=1).domain
    if not domain.startswith('http'):
        domain = "http://" + domain

    return domain

def notify_new_user_creation(user=None):
    subject=_("[DBAAS] a new user has just been created: %s" % user.username)
    template="new_user_notification"
    addr_from=Configuration.get_by_name("email_addr_from")
    addr_to=Configuration.get_by_name_as_list("new_user_notify_email")
    context={}
    context['user'] = user
    domain = get_domain()
    context['url'] = domain + reverse('admin:account_team_changelist')
    LOG.debug("user: %s | addr_from: %s | addr_to: %s" % (user, addr_from, addr_to))
    if user and addr_from and addr_to:
        send_mail_template(subject, template, addr_from, addr_to, fail_silently=False, attachments=None, context=context)
    else:
        LOG.warning("could not send email for new user creation")


def notify_team_change_for(user=None):
    LOG.info("Notifying team change for user %s" % user)
    subject=_("[DBAAS] your team has been updated!")
    template="team_change_notification"
    addr_from=Configuration.get_by_name("email_addr_from")
    if user.email:
        #addr_to=Configuration.get_by_name_as_list("new_user_notify_email") + [user.email]
        addr_to=[user.email]
        context={}
        context['user'] = user
        domain = get_domain()
        context['url'] = domain
        context['teams'] = [team.name for team in user.team_set.all()]
        if user and addr_from and addr_to:
            send_mail_template(subject, template, addr_from, addr_to, fail_silently=False, attachments=None, context=context)
        else:
            LOG.warning("could not send email for team change")
    else:
        LOG.warning("user %s has no email set and therefore cannot be notified!")

def databaseinfra_ending(context={}):
    LOG.info("Notifying DatabaseInfra ending")
    subject=_("[DBAAS] DatabaseInfra is almost full")
    template="infra_notification"
    addr_from=Configuration.get_by_name("email_addr_from")
    addr_to=Configuration.get_by_name_as_list("new_user_notify_email")

    context['domain'] = get_domain()

    send_mail_template(subject, template, addr_from, addr_to, fail_silently=False, attachments=None, context=context)

def database_usage(context={}):
    LOG.info("Notifying Database usage")
    subject=_("[DBAAS] Database is almost full")
    template="database_notification"
    addr_from=Configuration.get_by_name("email_addr_from")
    addr_to=[context["team"], Configuration.get_by_name_as_list("new_user_notify_email")]

    context['domain'] = get_domain()

    send_mail_template(subject, template, addr_from, addr_to, fail_silently=False, attachments=None, context=context)
    
    