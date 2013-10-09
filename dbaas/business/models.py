# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base.models import BaseModel


class Product(BaseModel):

    name = models.CharField(verbose_name=_("Product name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is product active"), default=True)
    slug = models.SlugField()

    def __unicode__(self):
        return "%s" % self.name


class Plan(BaseModel):

    name = models.CharField(verbose_name=_("Plan name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is plan active"), default=True)
    # engine_type = models.ForeignKey("base.EngineType", verbose_name='Engine Type', related_name='plans')

    def __unicode__(self):
        return "%s" % self.name


class PlanAttribute(BaseModel):

    name = models.CharField(verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey('business.Plan', related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)

simple_audit.register(Product, Plan, PlanAttribute)
