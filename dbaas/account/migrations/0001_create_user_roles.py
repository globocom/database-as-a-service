# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.contrib.auth.models import User, Group


class Migration(SchemaMigration):

    ROLES = ["role_dba", "role_regular"]

    def forwards(self, orm):

        [Group.objects.get_or_create(name=role) for role in Migration.ROLES]

    def backwards(self, orm):
        groups = Group.objects.filter(name__in=Migration.ROLES)
        [group.delete for group in groups]

    models = {

    }

    complete_apps = ['account']
