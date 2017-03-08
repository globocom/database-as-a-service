from django import forms
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response


class DatabaseOfferingWidget(forms.widgets.TextInput):

    def __init__(self, url, id, label, class_text=None, attrs=None, help_text=""):
        super(DatabaseOfferingWidget, self).__init__(attrs)
        self.help_text = help_text
        self.context = {
            'url': url,
            'id': id,
            'label': label,
        }
        if class_text:
            self.context['class'] = class_text

    def render(self, name, value, attrs=None):
        html = super(DatabaseOfferingWidget, self).render(name, value, attrs)

        button = render_to_response(
            'logical/database/widget_button.html', self.context
        )

        html = '{}{}{}<br><br>'.format(html, self.help_text, button.content)
        return mark_safe(html)
