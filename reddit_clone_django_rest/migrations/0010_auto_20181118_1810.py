# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-18 18:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reddit_clone_django_rest', '0009_auto_20181118_1805'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='posted_in',
        ),
        migrations.AddField(
            model_name='post',
            name='posted_in',
            field=models.ManyToManyField(to='reddit_clone_django_rest.Sub'),
        ),
    ]
