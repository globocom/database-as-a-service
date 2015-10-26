# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ExecutionPlan'
        db.create_table(u'analyzing_executionplan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('plan_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60, db_index=True)),
            ('metrics', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
            ('threshold', self.gf('django.db.models.fields.IntegerField')(default=50)),
            ('proccess_function', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('adapter', self.gf('django.db.models.fields.CharField')(max_length=150)),
        ))
        db.send_create_signal(u'analyzing', ['ExecutionPlan'])


    def backwards(self, orm):
        # Deleting model 'ExecutionPlan'
        db.delete_table(u'analyzing_executionplan')


    models = {
        u'analyzing.analyzerepository': {
            'Meta': {'unique_together': "(('analyzed_at', 'instance_name'),)", 'object_name': 'AnalyzeRepository'},
            'analyzed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'cpu_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'}),
            'email_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'engine_name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'environment_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'memory_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'analyzing.executionplan': {
            'Meta': {'object_name': 'ExecutionPlan'},
            'adapter': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metrics': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'proccess_function': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['analyzing']