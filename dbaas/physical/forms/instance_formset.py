# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

import logging

LOG = logging.getLogger(__name__)

class InstanceModelFormSet(BaseInlineFormSet):

    def get_endpoint(self, cleaned_data):
        return "%s:%s" % (cleaned_data.get('address'), cleaned_data.get('port'))

    def clean(self):
        super(InstanceModelFormSet, self).clean()

        for error in self.errors:
            if error:
                return

        completed = 0
        step = 0
        for cleaned_data in self.cleaned_data:
            # form has data and we aren't deleting it.
            if not cleaned_data:
                continue

            #LOG.debug(cleaned_data)
            is_deleted = cleaned_data.get('DELETE', False)
            databaseinfra = cleaned_data.get('databaseinfra', None)

            if databaseinfra and databaseinfra.engine.name == "mongodb":
                if step == 0: #clean endpoint
                    databaseinfra.endpoint = None
                    if not is_deleted:
                        databaseinfra.endpoint = self.get_endpoint(cleaned_data)
                elif step > 0 and databaseinfra:
                    if databaseinfra.endpoint and not is_deleted:
                        databaseinfra.endpoint = "%s,%s" % (databaseinfra.endpoint, 
                                                                self.get_endpoint(cleaned_data))
                    elif not databaseinfra.endpoint and not is_deleted:
                        databaseinfra.endpoint = self.get_endpoint(cleaned_data)

            if cleaned_data and not is_deleted:
                completed += 1

            cleaned_data['databaseinfra'] = databaseinfra
            step += 1

        
        # example custom validation across forms in the formset:
        if completed  == 0:
            raise ValidationError({'instances': _("Specify at least one valid instance")})

        #if step == 1, then set endpoint to the corresponding instance
        if step == 1:
            for cleaned_data in self.cleaned_data:

                if not cleaned_data:
                    continue
                
                # form has data and we aren't deleting it.
                is_deleted = cleaned_data.get('DELETE', False)
                databaseinfra = cleaned_data.get('databaseinfra', None)
                if not is_deleted:
                    databaseinfra.endpoint = self.get_endpoint(cleaned_data)
        else: #if has 2 or more instances and it is not mongodb, check if endpoint were set
            for cleaned_data in self.cleaned_data:

                if not cleaned_data:
                    continue

                databaseinfra = cleaned_data.get('databaseinfra', None)
                if databaseinfra.engine.name != "mongodb":
                    if not databaseinfra.endpoint:
                        raise ValidationError(_("You have 2 or more instances and dit not specify an endpoint"))