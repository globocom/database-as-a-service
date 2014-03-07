# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
from . import factory
from ..models import Team
from drivers import base

import logging

LOG = logging.getLogger(__name__)

class TeamTest(TestCase):

    def setUp(self):
        self.new_team = factory.TeamFactory()

    def test_create_new_team(self):
        """ 
        Test new Team creation 
        """
        self.assertTrue(self.new_team.pk)    

    def test_cant_create_a_new_user(self):
        self.team = Team()
        self.team.name = "Team1"
        self.team.role_id = factory.RoleFactory().pk
         
        self.assertFalse(self.team.save())
