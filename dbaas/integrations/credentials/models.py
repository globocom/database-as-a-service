# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from util.models import BaseModel
from django.db import models
from django.utils.translation import ugettext_lazy as _
from physical.models import Environment
from django_extensions.db.fields.encrypted import EncryptedCharField



class IntegrationType(BaseModel):
    CLOUDSTACK = 1
    NFSAAS = 2
    
    INTEGRATION_CHOICES = (
        (CLOUDSTACK, 'Cloud Stack'),
        (NFSAAS, 'NFS as a Service'),
    )
    name = models.CharField(verbose_name=_("Offering ID"),
                                         max_length=100,
                                         help_text="Integration Name")
    type = models.IntegerField(choices=INTEGRATION_CHOICES,
                                default=0)
    

class IntegrationCredential(BaseModel):

    user = models.CharField(verbose_name=_("User."),
                            max_length=100,
                            help_text=_("User used to authenticate."),
                            blank=False,
                            null=False)
    password = EncryptedCharField(verbose_name=_("Password"), max_length=255, blank=True, null=False)
    integration_type = models.ForeignKey(IntegrationType, related_name="integration_type", on_delete=models.PROTECT)
    token = models.CharField(verbose_name=_("Authentication Token"),
                            max_length=255,
                            blank=True,
                            null=True)
    secret = EncryptedCharField(verbose_name=_("Token"), max_length=255, blank=True, null=False)
    endpoint = models.CharField(verbose_name=_("Endpoint"),
                            max_length=255,
                            help_text=_("Usually it is in the form host:port. Authentication endpoint."),
                            blank=True,
                            null=True)
    environments = models.ManyToManyField(Environment)

    def __unicode__(self):
        return "%s (integration_type=%s)" % (self.user, self.integration_type)

    class Meta:
        permissions = (
            ("view_integrationcredential", "Can view integration credential."),
        )

