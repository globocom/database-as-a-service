# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AnalyzeRepository'
        db.create_table(u'analyzing_analyzerepository', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('analyzed_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('database_name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('instance_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('engine_name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('environment_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('cpu_alarm', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('memory_alarm', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'analyzing', ['AnalyzeRepository'])

        # Adding unique constraint on 'AnalyzeRepository', fields ['analyzed_at', 'instance_name']
        db.create_unique(u'analyzing_analyzerepository', ['analyzed_at', 'instance_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'AnalyzeRepository', fields ['analyzed_at', 'instance_name']
        db.delete_unique(u'analyzing_analyzerepository', ['analyzed_at', 'instance_name'])

        # Deleting model 'AnalyzeRepository'
        db.delete_table(u'analyzing_analyzerepository')


    models = {
        u'analyzing.analyzerepository': {
            'Meta': {'unique_together': "(('analyzed_at', 'instance_name'),)", 'object_name': 'AnalyzeRepository'},
            'analyzed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'cpu_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'engine_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'environment_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'memory_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['analyzing']