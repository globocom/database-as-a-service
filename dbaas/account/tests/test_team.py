# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.core.exceptions import ValidationError
from model_mommy import mommy

from account.models import Team
from account.views import emergency_contacts


class TeamTest(TestCase):

    def setUp(self):
        self.new_team = mommy.make_recipe(
            'account.team'
        )

    def test_create_new_team(self):
        self.assertTrue(self.new_team.pk)

    def test_cant_create_a_new_user(self):
        team = Team()
        team.name = "Team1"
        team.role_id = mommy.make_recipe(
            'account.role',
        ).pk
        team.organization_id = mommy.make(
            'Organization'
        ).pk
        self.assertFalse(team.save())

    def test_can_get_emergency_contacts_by_view(self):
        contacts_found = emergency_contacts(team_id=self.new_team.pk)
        self.assertEqual(self.new_team.emergency_contacts, contacts_found)

    def test_cannot_get_emergency_contacts_by_view_wrong_id(self):
        contacts_found = emergency_contacts(team_id=-1)
        self.assertIsNone(contacts_found)

    def test_cannot_get_emergency_contacts_by_view_invalid_id(self):
        contacts_found = emergency_contacts(team_id="")
        self.assertIsNone(contacts_found)

    def test_can_get_emergency_contacts_by_property(self):
        response = self.new_team.emergency_contacts
        self.assertEqual(response, self.new_team.contacts)

    def test_cannot_get_emergency_contacts_by_property(self):
        team = mommy.make_recipe(
            'account.team',
            contacts=None
        )
        response = team.emergency_contacts
        self.assertEqual(response, 'Not defined. Please, contact the team')

    def test_clean_does_not_raise_validation_error(self):
        team = mommy.make_recipe('account.team')
        self.assertIsNone(team.clean())

    def test_clean_raises_validation_error(self):
        team = mommy.make_recipe(
            'account.team',
            contacts=None
        )
        self.assertRaises(ValidationError, team.clean)

    def test_can_get_same_team_users(self):
        new_team2 = mommy.make_recipe('account.team')
        expected_users = sorted(mommy.make_recipe(
            'account.user',
            _quantity=10
        ), key=lambda u: u.id)

        new_team2.users.add(expected_users[0])
        for user in expected_users[0:6]:
            self.new_team.users.add(user)
        self.new_team.save()
        for user in expected_users[4:]:
            new_team2.users.add(user)
        new_team2.save()
        resulted_users = sorted(
            Team.users_at_same_team(expected_users[0]),
            key=lambda u: u.id
        )

        self.assertEqual(resulted_users, expected_users)

    def test_can_get_same_team_users_empty_user(self):
        resulted_users = set(Team.users_at_same_team(None))
        self.assertFalse(resulted_users)
