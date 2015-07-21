# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Configuration'
        db.create_table(u'system_configuration', (
            (u'id', self.gf('django.db.models.fields.AutoField')
             (primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=100)),
            ('value', self.gf('django.db.models.fields.CharField')
             (max_length=255)),
        ))
        db.send_create_signal(u'system', ['Configuration'])

    def backwards(self, orm):
        # Deleting model 'Configuration'
        db.delete_table(u'system_configuration')

    models = {
        u'system.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['system']
