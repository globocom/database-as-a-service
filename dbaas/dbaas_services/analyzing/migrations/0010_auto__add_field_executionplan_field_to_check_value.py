# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ExecutionPlan.field_to_check_value'
        db.add_column(u'analyzing_executionplan', 'field_to_check_value',
                      self.gf('django.db.models.fields.CharField')(default=None, unique=True, max_length=150),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ExecutionPlan.field_to_check_value'
        db.delete_column(u'analyzing_executionplan', 'field_to_check_value')


    models = {
        u'analyzing.analyzerepository': {
            'Meta': {'unique_together': "(('analyzed_at', 'instance_name'),)", 'object_name': 'AnalyzeRepository'},
            'analyzed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'cpu_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cpu_threshold': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'}),
            'databaseinfra_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'}),
            'email_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'engine_name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'environment_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'memory_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'memory_threshold': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'volume_alarm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'volume_threshold': ('django.db.models.fields.IntegerField', [], {'default': '50'})
        },
        u'analyzing.executionplan': {
            'Meta': {'object_name': 'ExecutionPlan'},
            'adapter': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'alarm_repository_attr': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'field_to_check_value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metrics': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'minimum_value': ('django.db.models.fields.IntegerField', [], {}),
            'plan_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'proccess_function': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'threshold_repository_attr': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['analyzing']