# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from reddit_clone_django_rest.app.models import User, Post, Sub, Account, Comment, Notification
from reddit_clone_django_rest.app.serializers import SubSerializer, PostSerializer
from reddit_clone_django_rest.app.services import notification_service
import reddit_clone_django_rest.app.constants as constants
from django.db.models import signals
from reddit_clone_django_rest.app.signals import create_comment_notifications, create_post_notifications

class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):

        # disconnect signals for unit testing Notification functions.
        # Reconnect where necessary. 
        signals.post_save.disconnect(create_comment_notifications, sender=Comment)
        signals.post_save.disconnect(create_post_notifications, sender=Post)

        client = APIClient()

        # create User
        cls.user = User.objects.create_user(
            username="cameron",
            password="123456"
        )

        #get token for requests
        cls.token = Token.objects.get(user__username="cameron").key

        # Create new account to supply as sub creator
        cls.account = Account.objects.get(id=cls.user.id)
        response = client.get('/accounts/' + str(cls.account.id) + '/')
        cls.account_url = json.loads(response.content)['url']

        # create Sub to post in, and fetch from api to get url property
        cls.sub = Sub.objects.create(title="Some New Sub", created_by=cls.account)
        url = reverse('sub-detail', kwargs={'slug': cls.sub.slug})
        response = client.get(url, format='json')
        cls.sub_url = response.json()['url']
        
        # Add user as an admin
        cls.sub.admins.add(cls.account)
        cls.sub.save()

        # create a post to comment on.
        cls.post = Post.objects.create(
            title = 'A new Post',
            author = cls.account,
            body_text = 'Some post text',
            posted_in = cls.sub
        )

    # Comment notifications

    def test_create_comment_notification(self):
        comment = Comment.objects.create(
            body_text  = "A new comment",
            author = self.account,
            post = self.post
        )

        notification_service.create_comment_notification(self.account, "A test notification", comment, constants.COMMENT_PARENT_AUTHOR)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "A test notification")

    def test_create_parent_comment_author_notification(self):
        parent_comment = Comment.objects.create(
            body_text  = "A new parent comment",
            author = self.account,
            post = self.post
        )
        comment = Comment.objects.create(
            body_text  = "A new comment",
            author = self.account,
            post = self.post,
            parent = parent_comment
        )

        notification_service.notify_parent_comment_author(comment, "cameron", self.sub.title)
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "cameron replied to your comment in Some New Sub")

    def test_create_post_author_notification(self):
        comment = Comment.objects.create(
            body_text  = "A new comment",
            author = self.account,
            post = self.post
        )
        notification_service.notify_post_author(comment, "ronnie", self.sub.title)
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "ronnie commented on your post in Some New Sub")


    def test_notify_op_is_post_author(self):
        comment = Comment.objects.create(
            body_text  = "A new comment",
            author = self.account,
            post = self.post
        )
        notification_service.notify_op(comment, "ronnie", self.sub.title)
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "ronnie commented on your post in Some New Sub")
    
    def test_notify_op_is_parent_comment_author(self):
        parent_comment = Comment.objects.create(
            body_text  = "A new parent comment",
            author = self.account,
            post = self.post
        )
        comment = Comment.objects.create(
            body_text  = "A new comment",
            author = self.account,
            post = self.post,
            parent = parent_comment
        )

        notification_service.notify_op(comment, "cameron", self.sub.title)
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "cameron replied to your comment in Some New Sub")

    def test_notify_mentioned_users(self):
        comment = Comment.objects.create(
            body_text  = "Hey @cameron, check out A new comment",
            author = self.account,
            post = self.post
        )

        notification_service.notify_mentioned_users(comment, "cameron", self.sub.title)
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().message, "cameron mentioned you in a comment in Some New Sub")

    def test_create_comment_notifications(self):
        comment = Comment.objects.create(
            body_text  = "Hey @cameron, check out A new comment",
            author = self.account,
            post = self.post
        )

        notification_service.create_comment_notifications(comment)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.all()[0].message, "cameron mentioned you in a comment in Some New Sub")
        self.assertEqual(Notification.objects.all()[1].message, "cameron commented on your post in Some New Sub")

    def test_notify_post_admins_on_new_post(self):
        notification_service.create_post_notifications(self.post)

        self.assertEqual(Notification.objects.count(), 1)

    def test_post_notifications_created_by_signals(self):

        # Reconnect post signal.
        signals.post_save.connect(create_post_notifications, sender=Post)

        url = reverse('post-list')
    
        data = { 'title': 'A test post', 'body_text': 'some text', 'posted_in': self.sub.id}
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)

