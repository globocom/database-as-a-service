from slugify import slugify as slugify_function
from django.contrib.auth.models import User


def slugify(string):
    return slugify_function(string, separator="_")


def make_db_random_password():
    return User.objects.make_random_password()
