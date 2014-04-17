# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EnvironmentAttr'
        db.create_table(u'dbmonitor_environmentattr', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('dbaas_environment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dbmonitor_environment_attributes', to=orm['physical.Environment'])),
            ('dbmonitor_environment', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'dbmonitor', ['EnvironmentAttr'])


    def backwards(self, orm):
        # Deleting model 'EnvironmentAttr'
        db.delete_table(u'dbmonitor_environmentattr')


    models = {
        u'dbmonitor.environmentattr': {
            'Meta': {'object_name': 'EnvironmentAttr'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dbaas_environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dbmonitor_environment_attributes'", 'to': u"orm['physical.Environment']"}),
            'dbmonitor_environment': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.environment': {
            'Meta': {'object_name': 'Environment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['dbmonitor']