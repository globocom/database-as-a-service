# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel


LOG = logging.getLogger(__name__)

class Configuration(BaseModel):

    name = models.CharField(verbose_name=_("Configuration name"), max_length=100, unique=True)
    value = models.CharField(verbose_name=_("Configuration value"), max_length=255)
    
    @classmethod
    def get_by_name(cls, name):
        try:
            return Configuration.objects.get(name=name).value
        except Configuration.DoesNotExist:
            LOG.warning("configuration %s not found" % name)
            return None
        except Exception, e:
            LOG.warning("ops.. could not retrieve configuration value for %s: " % (name, e))
            return None


class ConfigurationHolder(object):
    """This class holds the used configurations in the system"""
    
    email_addr_from=Configuration.get_by_name("email_addr_from")
    new_user_notify_email=Configuration.get_by_name("new_user_notify_email")