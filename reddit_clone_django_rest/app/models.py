# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save

class Account(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

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
    body_text = models.TextField(blank=True, null=True)
    body_html = models.TextField(blank=True, null=True)
    link_url = models.URLField(null=True, blank=True)
    link_preview_img = models.ImageField(upload_to='link_previews/', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    saved_by = models.ManyToManyField(Account, related_name='saved_posts')
    upvoted_by = models.ManyToManyField(Account, related_name='upvoted_posts', blank=True)
    downvoted_by = models.ManyToManyField(Account, related_name='downvoted_posts', blank=True)

    def __unicode__(self):
        return self.title + " - " + self.posted_in.title + " - " + self.author.user.username

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    class Meta:
        ordering = ('created',)

class Comment(models.Model):
    confidence = models.IntegerField(default=0, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Account, related_name="comments", on_delete=models.CASCADE, blank=True)
    slug = models.SlugField(max_length=200, blank=True)
    body_text = models.TextField()
    body_html = models.TextField()
    parent = models.ForeignKey('self', related_name="child", on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    saved_by = models.ManyToManyField(Account, related_name='saved_comments', blank=True)
    upvoted_by = models.ManyToManyField(Account, related_name='upvoted_comments', blank=True)
    downvoted_by = models.ManyToManyField(Account, related_name='downvoted_comments', blank=True)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return str(self.id)

# Create auth tokens for new accounts
@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)

