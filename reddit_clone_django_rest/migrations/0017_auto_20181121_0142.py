# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-21 01:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reddit_clone_django_rest', '0016_auto_20181121_0135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='reddit_clone_django_rest.Account'),
        ),
    ]
