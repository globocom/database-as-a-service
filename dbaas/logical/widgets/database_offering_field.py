from django import forms
from django.utils.safestring import mark_safe


class DatabaseOfferingWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
        html = super(DatabaseOfferingWidget, self).render(name, value, attrs)

        resize_link = """
             </br><a id="resizeDatabase" class="btn btn-primary" href=
             """ + self.attrs['database'].get_resize_url() + """>Resize VM</a >"""

        html_plus = """

            <style type="text/css">

                #resizeDatabase {
                    position: relative;
                    top: 5px
                }

            </style>
         """
        html = """{}{}{}""".format(html, resize_link, html_plus)

        return mark_safe(html)
