# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'TaskHistory.description'
        db.delete_column(u'notification_taskhistory', 'description')

        # Adding field 'TaskHistory.details'
        db.add_column(u'notification_taskhistory', 'details',
                      self.gf('django.db.models.fields.TextField')(
                          null=True, blank=True),
                      keep_default=False)

    def backwards(self, orm):
        # Adding field 'TaskHistory.description'
        db.add_column(u'notification_taskhistory', 'description',
                      self.gf('django.db.models.fields.TextField')(
                          null=True, blank=True),
                      keep_default=False)

        # Deleting field 'TaskHistory.details'
        db.delete_column(u'notification_taskhistory', 'details')

    models = {
        u'notification.taskhistory': {
            'Meta': {'object_name': 'TaskHistory'},
            'arguments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'context': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'task_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'task_status': ('django.db.models.fields.CharField', [], {'default': "u'PENDING'", 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['notification']
