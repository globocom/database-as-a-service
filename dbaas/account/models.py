# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel

LOG = logging.getLogger(__name__)

class Profile(BaseModel):
    user = models.OneToOneField(User)
    team = models.CharField(max_length=200)


#####################################################################################################
# SIGNALS
#####################################################################################################

#all users should be is_staff True
@receiver(pre_save, sender=User)
def user_pre_save(sender, **kwargs):
    user = kwargs.get('instance')
    if not user.is_staff:
        user.is_staff = True