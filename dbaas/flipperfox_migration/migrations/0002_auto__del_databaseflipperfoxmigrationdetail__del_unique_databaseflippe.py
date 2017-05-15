# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'DatabaseFlipperFoxMigrationDetail', fields ['database_flipperfox_migration', 'step', 'scheduled_for']
        db.delete_unique(u'flipperfox_migration_databaseflipperfoxmigrationdetail', ['database_flipperfox_migration_id', 'step', 'scheduled_for'])

        # Deleting model 'DatabaseFlipperFoxMigrationDetail'
        db.delete_table(u'flipperfox_migration_databaseflipperfoxmigrationdetail')

        # Deleting model 'DatabaseFlipperFoxMigration'
        db.delete_table(u'flipperfox_migration_databaseflipperfoxmigration')


    def backwards(self, orm):
        # Adding model 'DatabaseFlipperFoxMigrationDetail'
        db.create_table(u'flipperfox_migration_databaseflipperfoxmigrationdetail', (
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('is_migration_up', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('finished_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('scheduled_for', self.gf('django.db.models.fields.DateTimeField')()),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('step', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('celery_task_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('log', self.gf('django.db.models.fields.TextField')()),
            ('revoked_by', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('database_flipperfox_migration', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'details', to=orm['flipperfox_migration.DatabaseFlipperFoxMigration'])),
        ))
        db.send_create_signal(u'flipperfox_migration', ['DatabaseFlipperFoxMigrationDetail'])

        # Adding unique constraint on 'DatabaseFlipperFoxMigrationDetail', fields ['database_flipperfox_migration', 'step', 'scheduled_for']
        db.create_unique(u'flipperfox_migration_databaseflipperfoxmigrationdetail', ['database_flipperfox_migration_id', 'step', 'scheduled_for'])

        # Adding model 'DatabaseFlipperFoxMigration'
        db.create_table(u'flipperfox_migration_databaseflipperfoxmigration', (
            ('database', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'flipperfoxmigration', unique=True, to=orm['logical.Database'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('current_step', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'flipperfox_migration', ['DatabaseFlipperFoxMigration'])


    models = {
        
    }

    complete_apps = ['flipperfox_migration']