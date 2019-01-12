# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-23 23:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reddit_clone_django_rest', '0020_auto_20181121_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='downvoted_by',
            field=models.ManyToManyField(related_name='downvoted_comments', to='reddit_clone_django_rest.Account'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='upvoted_by',
            field=models.ManyToManyField(related_name='upvoted_comments', to='reddit_clone_django_rest.Account'),
        ),
        migrations.AlterField(
            model_name='sub',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subs_created', to='reddit_clone_django_rest.Account'),
        ),
        migrations.AlterField(
            model_name='sub',
            name='subscribers',
            field=models.ManyToManyField(blank=True, related_name='subbed_to', to='reddit_clone_django_rest.Account'),
        ),
    ]
