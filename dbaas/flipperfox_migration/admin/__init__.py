# -*- coding:utf-8 -*-
from django.contrib import admin
from ..models import DatabaseFlipperFoxMigration, DatabaseFlipperFoxMigrationDetail
from .databaseflipperfoxmigration import DatabaseFlipperFoxMigrationAdmin
from .databaseflipperfoxmigrationdetail import DatabaseFlipperFoxMigrationDetailAdmin

admin.site.register(DatabaseFlipperFoxMigration, DatabaseFlipperFoxMigrationAdmin)
admin.site.register(DatabaseFlipperFoxMigrationDetail,
                    DatabaseFlipperFoxMigrationDetailAdmin)
