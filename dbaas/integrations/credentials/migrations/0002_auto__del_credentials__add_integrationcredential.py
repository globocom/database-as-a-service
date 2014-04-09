# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Credentials'
        db.delete_table(u'credentials_credentials')

        # Removing M2M table for field environments on 'Credentials'
        db.delete_table(db.shorten_name(u'credentials_credentials_environments'))

        # Adding model 'IntegrationCredential'
        db.create_table(u'credentials_integrationcredential', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('integration_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'integration_type', on_delete=models.PROTECT, to=orm['credentials.IntegrationType'])),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('endpoint', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'credentials', ['IntegrationCredential'])

        # Adding M2M table for field environments on 'IntegrationCredential'
        m2m_table_name = db.shorten_name(u'credentials_integrationcredential_environments')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('integrationcredential', models.ForeignKey(orm[u'credentials.integrationcredential'], null=False)),
            ('environment', models.ForeignKey(orm[u'physical.environment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['integrationcredential_id', 'environment_id'])


    def backwards(self, orm):
        # Adding model 'Credentials'
        db.create_table(u'credentials_credentials', (
            ('integration_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'integration_type', on_delete=models.PROTECT, to=orm['credentials.IntegrationType'])),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('endpoint', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'credentials', ['Credentials'])

        # Adding M2M table for field environments on 'Credentials'
        m2m_table_name = db.shorten_name(u'credentials_credentials_environments')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credentials', models.ForeignKey(orm[u'credentials.credentials'], null=False)),
            ('environment', models.ForeignKey(orm[u'physical.environment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['credentials_id', 'environment_id'])

        # Deleting model 'IntegrationCredential'
        db.delete_table(u'credentials_integrationcredential')

        # Removing M2M table for field environments on 'IntegrationCredential'
        db.delete_table(db.shorten_name(u'credentials_integrationcredential_environments'))


    models = {
        u'credentials.integrationcredential': {
            'Meta': {'object_name': 'IntegrationCredential'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'endpoint': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['physical.Environment']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'integration_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'integration_type'", 'on_delete': 'models.PROTECT', 'to': u"orm['credentials.IntegrationType']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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