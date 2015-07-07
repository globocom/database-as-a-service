# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from util.models import BaseModel
import logging

LOG = logging.getLogger(__name__)


class ExtraDns(BaseModel):

    database = models.ForeignKey('logical.Database',
                                 related_name="extra_dns",
                                 unique=False, null=False, blank=False,
                                 on_delete=models.CASCADE)

    dns = models.CharField(verbose_name=_("DNS"), max_length=200, null=False, blank=False,)

    def __unicode__(self):
        return u"Extra dns: {} for database : {}".format(self.dns, self.database)