# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.utils.html import format_html


class PoolAdmin(admin.ModelAdmin):

    list_display = ["name", 'environment', 'get_team_names']
    filter_horizontal = ['teams']
    list_filter = ('environment',)
    search_fields = ('name', 'teams__name')

    def get_team_names(self, pool):
        teams = pool.teams.all()
        team_html = []
        if teams:
            team_html.append("<ul>")
            for team in teams:
                team_html.append("<li>%s</li>" % team.name)
            team_html.append("</ul>")
            return format_html("".join(team_html))
        else:
            return "N/A"

    get_team_names.short_description = "Team(s)"
