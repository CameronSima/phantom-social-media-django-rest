# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from reddit_clone_django_rest.app.constants import NOTIFICATION_TYPES, VOTE_TYPES

class Account(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    @receiver(post_save, sender=User)
    def create_user_account(sender, instance, created, **kwargs):
        if created:
            Account.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_account(sender, instance, **kwargs):
        instance.account.save()

    def __unicode__(self):
        return self.user.username

    class Meta:
        ordering = ('created',)

class Sub(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=500, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=200, blank=True)
    subscribers = models.ManyToManyField(Account, blank=True, related_name="subbed_to")
    admins = models.ManyToManyField(Account, blank=True, related_name="admin_of")
    created_by = models.ForeignKey(Account, related_name="subs_created", on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    send_new_post_notifications = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Sub, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-created',)

class Post(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    posted_in = models.ForeignKey(Sub, related_name="posts")
    author = models.ForeignKey(Account, related_name="posts", on_delete=models.CASCADE)
    title = models.CharField(max_length=500, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=200, blank=True)
    body_text = models.TextField(blank=False, null=False)
    body_html = models.TextField(blank=True, null=True)
    link_url = models.URLField(null=True, blank=True)
    link_preview_img = models.ImageField(upload_to='link_previews/', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    saved_by = models.ManyToManyField(Account, related_name='saved_posts')
    is_visible = models.BooleanField(default=True)

    scores_last_generated = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)
    hot = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    controversy = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    confidence = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)

    def __unicode__(self):
        return self.title + " - " + self.posted_in.title + " - " + self.author.user.username

    def save(self, *args, **kwargs):
        print kwargs
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    class Meta:
        ordering = ('created',)

class Comment(MPTTModel):
    confidence = models.IntegerField(default=0, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Account, related_name="comments", on_delete=models.CASCADE, blank=True)
    slug = models.SlugField(max_length=200, blank=True)
    body_text = models.TextField()
    body_html = models.TextField()
    parent = TreeForeignKey('self', related_name="children", on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    saved_by = models.ManyToManyField(Account, related_name='saved_comments')

    scores_last_generated = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)
    hot = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    controversy = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    confidence = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return str(self.id)


# Create auth tokens for new accounts
@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Notification(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Account, related_name="notifications", on_delete=models.CASCADE, blank=False)
    seen = models.BooleanField(default=False)
    message = models.TextField(blank=False, null=False)
    link = models.TextField(blank=False, null=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(choices=NOTIFICATION_TYPES, blank=False, null=False, max_length=30)

class Vote(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    date_placed = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Account, related_name="votes", on_delete=models.CASCADE, blank=False)
    direction = models.IntegerField(choices=VOTE_TYPES, default=0)
    post = models.ForeignKey(Post, related_name="votes", on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, related_name="votes", on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.date_placed = datetime.now()
        super(Vote, self).save(*args, **kwargs)