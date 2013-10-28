# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField

from util.models import BaseModel
from .helper import find_ldap_groups_from_user

LOG = logging.getLogger(__name__)


def sync_ldap_groups_with_user(user=None):
    """
    Sync ldap groups (aka team) with the user
    """
    ldap_groups = find_ldap_groups_from_user(username=user.username)
    groups = Group.objects.filter(name__in=ldap_groups).exclude(user=user)
    LOG.info("LDAP's team created in the system and not set to user %s: %s" % (user, groups))
    if groups:
        groups[0].user_set.add(user)
        LOG.info("group %s added to user %s" % (groups[0], user))



#####################################################################################################
# SIGNALS
#####################################################################################################

#all users should be is_staff True
@receiver(pre_save, sender=User)
def user_pre_save(sender, **kwargs):
    user = kwargs.get('instance')
    LOG.debug("user pre save signal")
    if not user.is_staff:
        user.is_staff = True


@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    user = kwargs.get('instance')
    LOG.debug("user post save signal")
    sync_ldap_groups_with_user(user=user)



