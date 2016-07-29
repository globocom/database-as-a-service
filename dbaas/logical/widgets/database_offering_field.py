from django import forms
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response


class DatabaseOfferingWidget(forms.widgets.TextInput):

    def __init__(self, url, id, label, attrs=None):
        super(DatabaseOfferingWidget, self).__init__(attrs)
        self.context = {
            'url': url,
            'id': id,
            'label': label
        }

    def render(self, name, value, attrs=None):
        html = super(DatabaseOfferingWidget, self).render(name, value, attrs)

        button = render_to_response(
            'logical/database/widget_button.html', self.context
        )

        html = '{}{}'.format(html, button.content)
        return mark_safe(html)
