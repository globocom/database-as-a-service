from slugify import slugify as slugify_function
from django.contrib.auth.models import User
from django.http import HttpResponse
import json


def slugify(string):
    return slugify_function(string, separator="_")


def make_db_random_password():
    return User.objects.make_random_password()

def as_json(f):
    def wrapper(request, *args, **kw):
        output = f(request, *args, **kw)
        if isinstance(output, HttpResponse):
            return output
        elif isinstance(output, basestring):
            return HttpResponse(output, content_type="text/plain")
        output = json.dumps(output, indent=4)
        return HttpResponse(output, content_type="application/json")
    return wrapper
