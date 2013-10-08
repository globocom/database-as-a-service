# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Product'
        db.create_table(u'business_product', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal(u'business', ['Product'])

        # Adding model 'Plan'
        db.create_table(u'business_plan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'plans', to=orm['base.EngineType'])),
        ))
        db.send_create_signal(u'business', ['Plan'])

        # Adding M2M table for field environment on 'Plan'
        m2m_table_name = db.shorten_name(u'business_plan_environment')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('plan', models.ForeignKey(orm[u'business.plan'], null=False)),
            ('environment', models.ForeignKey(orm[u'base.environment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['plan_id', 'environment_id'])

        # Adding model 'PlanAttribute'
        db.create_table(u'business_planattribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'plan_attributes', to=orm['business.Plan'])),
        ))
        db.send_create_signal(u'business', ['PlanAttribute'])


    def backwards(self, orm):
        # Deleting model 'Product'
        db.delete_table(u'business_product')

        # Deleting model 'Plan'
        db.delete_table(u'business_plan')

        # Removing M2M table for field environment on 'Plan'
        db.delete_table(db.shorten_name(u'business_plan_environment'))

        # Deleting model 'PlanAttribute'
        db.delete_table(u'business_planattribute')


    models = {
        u'base.enginetype': {
            'Meta': {'object_name': 'EngineType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'base.environment': {
            'Meta': {'object_name': 'Environment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'business.plan': {
            'Meta': {'object_name': 'Plan'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plans'", 'to': u"orm['base.EngineType']"}),
            'environment': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'plans'", 'symmetrical': 'False', 'to': u"orm['base.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'business.planattribute': {
            'Meta': {'object_name': 'PlanAttribute'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plan_attributes'", 'to': u"orm['business.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'business.product': {
            'Meta': {'object_name': 'Product'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['business']