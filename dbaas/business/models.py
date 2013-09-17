# coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base.models import BaseModel


class Product(BaseModel):

    name = models.CharField(verbose_name=_("product_name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("product_is_active"), default=True)
    slug = models.SlugField()

    def __unicode__(self):
        return u"%s" % self.name


class Plan(BaseModel):

    name = models.CharField(verbose_name=_("plan_name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("plan_is_active"), default=True)
    environment = models.ManyToManyField("base.Environment", related_name="plans")

    def __unicode__(self):
        return u"%s" % self.name


class PlanAttribute(BaseModel):

    name = models.CharField(verbose_name=_("plan_attribute_name"), max_length=200)
    value = models.CharField(verbose_name=_("plan_attribute_value"), max_length=200)
    plan = models.ForeignKey('business.Plan', related_name="plan_attributes")
