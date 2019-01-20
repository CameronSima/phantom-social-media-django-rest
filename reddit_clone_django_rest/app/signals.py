import sys
from django.db.models.signals import post_save
from django.dispatch import receiver
from reddit_clone_django_rest.app.models import Notification, Post, Comment
from reddit_clone_django_rest.app.services import notification_service

@receiver(post_save, sender=Comment)
def create_comment_notifications(sender, instance, **kwargs):
    notification_service.create_comment_notifications(instance)

@receiver(post_save, sender=Post)
def create_post_notifications(sender, instance, **kwargs):
    notification_service.create_post_notifications(instance)
