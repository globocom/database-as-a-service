from django import forms
from django.core.validators import MinValueValidator
from ..models import DiskOffering

class DiskOfferingForm(forms.ModelForm):

    size_gb = forms.FloatField(
        label='Size GB', validators=[MinValueValidator(0.1)]
    )

    available_size_gb = forms.FloatField(
        label='Available Size GB', validators=[MinValueValidator(0.1)]
    )

    class Meta:
        model = DiskOffering
        fields = ("name", "size_gb", "available_size_gb")

    def __init__(self, *args, **kwargs):
        super(DiskOfferingForm, self).__init__(*args, **kwargs)
        self.initial['size_gb'] = self.instance.size_gb()
        self.initial['available_size_gb'] = self.instance.available_size_gb()

    def clean(self):
        size_gb = self.cleaned_data.get("size_gb")
        available_size_gb = self.cleaned_data.get("available_size_gb")
        if available_size_gb > size_gb:
            message = "The available size should be lower than disk size."
            self._errors["available_size_gb"] = self.error_class([message])

        return self.cleaned_data
