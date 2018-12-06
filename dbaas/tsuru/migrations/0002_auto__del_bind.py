# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Bind'
        db.delete_table(u'tsuru_bind')


    def backwards(self, orm):
        # Adding model 'Bind'
        db.create_table(u'tsuru_bind', (
            ('service_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('service_hostname', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('databaseinfra', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'binds', null=True, to=orm['physical.DatabaseInfra'], on_delete=models.PROTECT, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'tsuru', ['Bind'])


    models = {
        
    }

    complete_apps = ['tsuru']