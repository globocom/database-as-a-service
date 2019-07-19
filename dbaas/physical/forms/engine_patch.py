from django import forms
from django.forms.models import BaseInlineFormSet

from ..models import EnginePatch


class EnginePatchFormset(BaseInlineFormSet):

    def clean(self):
        """This method validates duplicated initial_patch given for an
        EnginePatch formset. ValidationError is not triggered when an objects
        is being deleted.
        """
        super(EnginePatchFormset, self).clean()

        count = 0
        for form in self.forms:
            cleaned_data = form.cleaned_data
            if cleaned_data and cleaned_data.get('is_initial_patch'):
                if not cleaned_data.get('DELETE'):
                    count += 1
        if count > 1:
            raise forms.ValidationError('You must have only one initial_patch')

    class Meta:
        model = EnginePatch
        fields = ('patch_version', 'is_initial_patch', 'patch_path')
