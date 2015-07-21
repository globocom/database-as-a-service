# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Maintenance'
        db.create_table(u'maintenance_maintenance', (
            (u'id', self.gf('django.db.models.fields.AutoField')
             (primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('scheduled_for', self.gf(
                'django.db.models.fields.DateTimeField')()),
            ('main_script', self.gf('django.db.models.fields.TextField')()),
            ('rollback_script', self.gf('django.db.models.fields.TextField')
             (null=True, blank=True)),
            ('check_script', self.gf('django.db.models.fields.TextField')
             (null=True, blank=True)),
            ('host_query', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'maintenance', ['Maintenance'])

        # Adding model 'HostMaintenance'
        db.create_table(u'maintenance_hostmaintenance', (
            (u'id', self.gf('django.db.models.fields.AutoField')
             (primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')
             (auto_now=True, blank=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('finished_at', self.gf(
                'django.db.models.fields.DateTimeField')()),
            ('main_log', self.gf('django.db.models.fields.TextField')()),
            ('rollback_log', self.gf('django.db.models.fields.TextField')
             (null=True, blank=True)),
            ('check_log', self.gf('django.db.models.fields.TextField')
             (null=True, blank=True)),
            ('status', self.gf(
                'django.db.models.fields.IntegerField')(default=4)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name=u'host_maintenance', to=orm['physical.Host'])),
            ('maintenance', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name=u'maintenance', to=orm['maintenance.Maintenance'])),
        ))
        db.send_create_signal(u'maintenance', ['HostMaintenance'])

    def backwards(self, orm):
        # Deleting model 'Maintenance'
        db.delete_table(u'maintenance_maintenance')

        # Deleting model 'HostMaintenance'
        db.delete_table(u'maintenance_hostmaintenance')

    models = {
        u'maintenance.hostmaintenance': {
            'Meta': {'object_name': 'HostMaintenance'},
            'check_log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'host_maintenance'", 'to': u"orm['physical.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_log': ('django.db.models.fields.TextField', [], {}),
            'maintenance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'maintenance'", 'to': u"orm['maintenance.Maintenance']"}),
            'rollback_log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'maintenance.maintenance': {
            'Meta': {'object_name': 'Maintenance'},
            'check_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'host_query': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_script': ('django.db.models.fields.TextField', [], {}),
            'rollback_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_for': ('django.db.models.fields.DateTimeField', [], {}),
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
