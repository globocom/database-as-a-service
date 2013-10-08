# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Instance.product'
        db.add_column(u'base_instance', 'product',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'instances', null=True, on_delete=models.PROTECT, to=orm['business.Product']),
                      keep_default=False)

        # Adding field 'Instance.plan'
        db.add_column(u'base_instance', 'plan',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name=u'instances', on_delete=models.PROTECT, to=orm['business.Plan']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Instance.product'
        db.delete_column(u'base_instance', 'product_id')

        # Deleting field 'Instance.plan'
        db.delete_column(u'base_instance', 'plan_id')


    models = {
        u'base.credential': {
            'Meta': {'object_name': 'Credential'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'database': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'credentials'", 'to': u"orm['base.Database']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'base.database': {
            'Meta': {'object_name': 'Database'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databases'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Instance']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'base.engine': {
            'Meta': {'unique_together': "((u'version', u'engine_type'),)", 'object_name': 'Engine'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'engines'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
        u'base.instance': {
            'Meta': {'object_name': 'Instance'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Engine']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'node': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.Node']", 'unique': 'True', 'on_delete': 'models.PROTECT'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'on_delete': 'models.PROTECT', 'to': u"orm['business.Plan']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'instances'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['business.Product']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'base.node': {
            'Meta': {'unique_together': "((u'address', u'port'),)", 'object_name': 'Node'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'nodes'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'2'", 'max_length': '2'}),
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

    complete_apps = ['base']