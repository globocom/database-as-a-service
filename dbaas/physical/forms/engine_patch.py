from django import forms
from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.forms.util import ErrorList

from ..models import EnginePatch, Engine


class EnginePatchForm(forms.ModelForm):

    def clean(self):
        """This method validates patch_path as required field when the form is
        not checked as Delete or is_initial_patch = True. The error message is
        added directly into the field.
        """
        super(EnginePatchForm, self).clean()

        is_initial_patch = self.cleaned_data.get('is_initial_patch')
        patch_path = self.cleaned_data.get('patch_path')
        is_delete = self.cleaned_data.get('DELETE')

        if not is_initial_patch:
            if not patch_path and not is_delete:
                if 'patch_path' not in self._errors:
                    self._errors['patch_path'] = ErrorList()
                self._errors['patch_path'].append(
                    'Only an initial patch can have blank path!'
                )

        return self.cleaned_data

    class Meta:
        model = EnginePatch
        fields = (
            'patch_version', 'is_initial_patch',
            'patch_path', 'required_disk_size_gb'
        )


class EnginePatchFormset(BaseInlineFormSet):

    def clean(self):
        """This method validates whether there is a duplicated is_initial_patch
        or not and if a engine patch is not provided. ValidationError is not
        triggered when an object is being deleted.
        """
        super(EnginePatchFormset, self).clean()

        count = 0
        for form in self.forms:
            if form.cleaned_data:
                if form.cleaned_data.get('is_initial_patch'):
                    if not form.cleaned_data.get('DELETE'):
                        count += 1

        if count == 0:
            raise forms.ValidationError(
                'You must select at least one initial engine patch'
            )
        if count > 1:
            raise forms.ValidationError(
                'You must have only one initial engine patch'
            )


engine_patch_formset = inlineformset_factory(
    Engine,
    EnginePatch,
    formset=EnginePatchFormset
)
