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

# class Team(BaseModel):
#     name = models.CharField(verbose_name=_("Team name"), max_length=200, unique=True)
#     user = models.ForeignKey(User, related_name="teams", null=True, blank=True)
#     is_active = models.BooleanField(verbose_name=_("Is team active"), default=True)
# 
#     def __unicode__(self):
#         return "%s" % self.name
# 
# class Profile(BaseModel):
#     user = models.OneToOneField(User)
#     team = models.CharField(verbose_name=_("Team name"), max_length=200)
#     #team = models.OneToOneField(Team)
#     
#     def __unicode__(self):
#         return "%s | %s" % (self.user.username, self.team.name)


#####################################################################################################
# SIGNALS
#####################################################################################################

#all users should be is_staff True
@receiver(pre_save, sender=User)
def user_pre_save(sender, **kwargs):
    user = kwargs.get('instance')
    if not user.is_staff:
        user.is_staff = True


