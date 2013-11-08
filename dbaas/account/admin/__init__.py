# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.contrib.auth.models import User, Group

from ..models import Team, Role, AccountUser

from .user import UserAdmin
from .role import RoleAdmin
from .team import TeamAdmin

# from ..models import Profile
# 
# # Define an inline admin descriptor for Profile model
# # which acts a bit like a singleton
# class ProfileInline(admin.StackedInline):
#     model = Profile
#     can_delete = False
#     verbose_name_plural = 'Profile'
# 
# # Define a new User admin
# class UserAdmin(UserAdmin):
#     inlines = (ProfileInline, )
# 
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(AccountUser, UserAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Team, TeamAdmin)
