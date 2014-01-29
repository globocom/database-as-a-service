# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
    """Base model class"""

    created_at = models.DateTimeField(verbose_name=_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated_at"), auto_now=True)

    class Meta:
        abstract = True

    def __unicode__(self):

        if hasattr(self, 'name'):
            return "%s" % self.name
        elif hasattr(self, '__unicode__'):
            #return super(BaseModel, self).__unicode__()
            return self.__unicode__()
