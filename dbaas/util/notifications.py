# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from email_extras.utils import send_mail, send_mail_template
from system.models import Configuration, ConfigurationHolder

LOG = logging.getLogger(__name__)


def notify_new_user_creation(user=None):
    subject=_("[DBAAS] a new user has just been created: %s" % user.username)
    template="new_user_notification"
    addr_from=ConfigurationHolder.email_addr_from
    addr_to=ConfigurationHolder.new_user_notify_email
    context={}
    context['user'] = user
    domain = Site.objects.get(id=1).domain
    if not domain.startswith('http'):
        domain = "http://" + domain
    context['url'] = domain + reverse('admin:account_team_changelist')
    LOG.debug("user: %s | addr_from: %s | addr_to: %s" % (user, addr_from, addr_to))
    if user and addr_from and addr_to:
        send_mail_template(subject, template, addr_from, addr_to, fail_silently=False, attachments=None, context=context)
    else:
        LOG.warning("could not send email for new user creation")
