from django.contrib import admin
from django.contrib.flatpages.models import FlatPage

from .flat_page import FlatPageAdmin


# We have to unregister the normal admin, and then reregister ours
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
