# -*- coding: utf-8 -*-
import logging
from django.forms import models
from ..models import DatabaseRegionMigrationDetail

LOG = logging.getLogger(__name__)


class DatabaseRegionMigrationDetailForm(models.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DatabaseRegionMigrationDetailForm, self).__init__(*args, **kwargs)
    
    class Meta:
        model = DatabaseRegionMigrationDetail