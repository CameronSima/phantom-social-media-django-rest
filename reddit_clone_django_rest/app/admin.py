# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from reddit_clone_django_rest.app.models import Account, User, Post, Comment, Sub
from django_celery_beat.models import PeriodicTask, IntervalSchedule

# Register your models here.
class Admin(admin.AdminSite):
    site_header = "Phantom"

admin_site = Admin(name='My Admin')
admin_site.register(Account)
admin_site.register(Sub)
admin_site.register(Comment)
admin_site.register(Post)
admin_site.register(User)
admin_site.register(PeriodicTask)
admin_site.register(IntervalSchedule)
