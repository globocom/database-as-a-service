# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms import models
from django import forms
from ..models import Project


class ProjectForm(models.ModelForm):
    class Meta:
        model = Project
        widgets = {
            'slug': forms.HiddenInput(),
        }
