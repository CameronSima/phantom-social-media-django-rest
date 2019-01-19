# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-01-19 16:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.IntegerField(blank=True, default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('slug', models.SlugField(blank=True, max_length=200)),
                ('body_text', models.TextField()),
                ('body_html', models.TextField()),
                ('author', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='app.Account')),
                ('downvoted_by', models.ManyToManyField(blank=True, related_name='downvoted_comments', to='app.Account')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child', to='app.Comment')),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('seen', models.BooleanField(default=False)),
                ('message', models.TextField()),
                ('link', models.TextField()),
                ('type', models.CharField(choices=[('POST_AUTHOR', 'post_author'), ('COMMENT_PARENT_AUTHOR', 'comment_parent_author'), ('MENTIONED_USER', 'mentioned_user')], max_length=30)),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Comment')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=500, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=200)),
                ('body_text', models.TextField()),
                ('body_html', models.TextField(blank=True, null=True)),
                ('link_url', models.URLField(blank=True, null=True)),
                ('link_preview_img', models.ImageField(blank=True, null=True, upload_to='link_previews/')),
                ('image_url', models.URLField(blank=True, null=True)),
                ('is_private', models.BooleanField(default=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='app.Account')),
                ('downvoted_by', models.ManyToManyField(blank=True, related_name='downvoted_posts', to='app.Account')),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='Sub',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=500, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=200)),
                ('is_default', models.BooleanField(default=False)),
                ('admins', models.ManyToManyField(blank=True, related_name='admin_of', to='app.Account')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subs_created', to='app.Account')),
                ('subscribers', models.ManyToManyField(blank=True, related_name='subbed_to', to='app.Account')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.AddField(
            model_name='post',
            name='posted_in',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='app.Sub'),
        ),
        migrations.AddField(
            model_name='post',
            name='saved_by',
            field=models.ManyToManyField(related_name='saved_posts', to='app.Account'),
        ),
        migrations.AddField(
            model_name='post',
            name='upvoted_by',
            field=models.ManyToManyField(blank=True, related_name='upvoted_posts', to='app.Account'),
        ),
        migrations.AddField(
            model_name='notification',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Post'),
        ),
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='app.Account'),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='app.Post'),
        ),
        migrations.AddField(
            model_name='comment',
            name='saved_by',
            field=models.ManyToManyField(blank=True, related_name='saved_comments', to='app.Account'),
        ),
        migrations.AddField(
            model_name='comment',
            name='upvoted_by',
            field=models.ManyToManyField(blank=True, related_name='upvoted_comments', to='app.Account'),
        ),
    ]
