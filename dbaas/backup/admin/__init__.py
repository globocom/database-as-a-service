# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..models import Snapshot
from .snapshot import SnapshotAdmin


admin.site.register(Snapshot, SnapshotAdmin)
