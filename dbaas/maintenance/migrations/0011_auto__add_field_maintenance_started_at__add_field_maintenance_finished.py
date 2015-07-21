# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Maintenance.started_at'
        db.add_column(u'maintenance_maintenance', 'started_at',
                      self.gf('django.db.models.fields.DateTimeField')(
                          null=True),
                      keep_default=False)

        # Adding field 'Maintenance.finished_at'
        db.add_column(u'maintenance_maintenance', 'finished_at',
                      self.gf('django.db.models.fields.DateTimeField')(
                          null=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Maintenance.started_at'
        db.delete_column(u'maintenance_maintenance', 'started_at')

        # Deleting field 'Maintenance.finished_at'
        db.delete_column(u'maintenance_maintenance', 'finished_at')

    models = {
        u'maintenance.hostmaintenance': {
            'Meta': {'unique_together': "((u'host', u'maintenance'),)", 'object_name': 'HostMaintenance', 'index_together': "[[u'host', u'maintenance']]"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'host_maintenance'", 'to': u"orm['physical.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'maintenance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'maintenance'", 'to': u"orm['maintenance.Maintenance']"}),
            'rollback_log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'maintenance.maintenance': {
            'Meta': {'object_name': 'Maintenance'},
            'affected_hosts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'host_query': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_script': ('django.db.models.fields.TextField', [], {}),
            'maximum_workers': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'query_error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rollback_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_for': ('django.db.models.fields.DateTimeField', [], {'unique': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.host': {
            'Meta': {'object_name': 'Host'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monitor_url': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['maintenance']
