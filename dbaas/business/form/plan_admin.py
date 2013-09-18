import logging
from django.utils.translation import ugettext_lazy as _
from django import forms

log = logging.getLogger(__name__)


class PlanAttributeInlineFormset(forms.models.BaseInlineFormSet):

    def clean(self):
        # get forms that actually have valid data
        count = 0
        for form in self.forms:
            try:
                if form.cleaned_data:
                    count += 1
            except AttributeError:
                # annoyingly, if a subform is invalid Django explicity raises
                # an AttributeError for cleaned_data
                pass
        if count < 1:
            log.warning(u"%s" % _("You must have at least one plan attribute"))
            raise forms.ValidationError(_("You must have at least one plan attribute"))
        