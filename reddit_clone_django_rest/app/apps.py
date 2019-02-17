# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

class AappConfig(AppConfig):
    name = 'reddit_clone_django_rest.app'
    label = 'app'

    def ready(self):
        import reddit_clone_django_rest.app.signals
        # from reddit_clone_django_rest.app.scripts import FakeData
        # FakeData().create_fake_data(2, 5, 10, True)
        
