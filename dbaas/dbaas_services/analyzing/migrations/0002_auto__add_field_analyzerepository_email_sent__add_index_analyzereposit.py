# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'AnalyzeRepository.email_sent'
        db.add_column(u'analyzing_analyzerepository', 'email_sent',
                      self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True),
                      keep_default=False)

        # Adding index on 'AnalyzeRepository', fields ['engine_name']
        db.create_index(u'analyzing_analyzerepository', ['engine_name'])

        # Adding index on 'AnalyzeRepository', fields ['environment_name']
        db.create_index(u'analyzing_analyzerepository', ['environment_name'])

        # Adding index on 'AnalyzeRepository', fields ['instance_name']
        db.create_index(u'analyzing_analyzerepository', ['instance_name'])

        # Adding index on 'AnalyzeRepository', fields ['analyzed_at']
        db.create_index(u'analyzing_analyzerepository', ['analyzed_at'])

        # Adding index on 'AnalyzeRepository', fields ['database_name']
        db.create_index(u'analyzing_analyzerepository', ['database_name'])


    def backwards(self, orm):
        # Removing index on 'AnalyzeRepository', fields ['database_name']
        db.delete_index(u'analyzing_analyzerepository', ['database_name'])

        # Removing index on 'AnalyzeRepository', fields ['analyzed_at']
        db.delete_index(u'analyzing_analyzerepository', ['analyzed_at'])

        # Removing index on 'AnalyzeRepository', fields ['instance_name']
        db.delete_index(u'analyzing_analyzerepository', ['instance_name'])

        # Removing index on 'AnalyzeRepository', fields ['environment_name']
        db.delete_index(u'analyzing_analyzerepository', ['environment_name'])

        # Removing index on 'AnalyzeRepository', fields ['engine_name']
        db.delete_index(u'analyzing_analyzerepository', ['engine_name'])

        # Deleting field 'AnalyzeRepository.email_sent'
        db.delete_column(u'analyzing_analyzerepository', 'email_sent')


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
        }
    }

    complete_apps = ['analyzing']