# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from util.models import BaseModel
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from dbaas_dbmonitor.provider import DBMonitorProvider
import logging

LOG = logging.getLogger(__name__)


class ExtraDns(BaseModel):

    database = models.ForeignKey('logical.Database',
                                 related_name="extra_dns",
                                 unique=False, null=False, blank=False,
                                 on_delete=models.CASCADE)

    dns = models.CharField(verbose_name=_("DNS"), max_length=200, null=False, blank=False,)

    class Meta:
        permissions = (
            ("view_extradns", "Can view extra dns"),
        )

    def __unicode__(self):
        return u"Extra dns: {} for database : {}".format(self.dns, self.database)


@receiver(post_save, sender=ExtraDns)
def extra_dns_post_save(sender, **kwargs):
    """
        extra dns post save signal. Inserts extra dns on dbmonitor's database
    """
    LOG.debug("extra_dns post-save triggered")

    extra_dns = kwargs.get("instance")
    is_new = kwargs.get("created")

    if is_new:
        database = extra_dns.database
        DBMonitorProvider().insert_extra_dns(database=database, extra_dns=extra_dns.dns)


@receiver(post_delete, sender=ExtraDns)
def extra_dns_post_delete(sender, **kwargs):
    """
        extra dns post delete signal. Delete extra dns on dbmonitor's database
    """
    LOG.debug("extra_dns post-delete triggered")

    extra_dns = kwargs.get("instance")
    database = extra_dns.database

    DBMonitorProvider().remove_extra_dns(database=database, extra_dns=extra_dns.dns)
