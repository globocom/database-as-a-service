# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'IntegrationCredential.project'
        db.add_column(u'credentials_integrationcredential', 'project',
                      self.gf('django.db.models.fields.CharField')(default='proj', max_length=255),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'IntegrationCredential.project'
        db.delete_column(u'credentials_integrationcredential', 'project')


    models = {
        u'credentials.integrationcredential': {
            'Meta': {'object_name': 'IntegrationCredential'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'endpoint': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['physical.Environment']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'integration_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'integration_type'", 'on_delete': 'models.PROTECT', 'to': u"orm['credentials.IntegrationType']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'credentials.integrationtype': {
            'Meta': {'object_name': 'IntegrationType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
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

    complete_apps = ['credentials']