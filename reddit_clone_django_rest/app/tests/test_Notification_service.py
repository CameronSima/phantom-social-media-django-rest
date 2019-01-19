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

class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
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
        response = client.get('/subs/' + str(cls.sub.id) + '/')
        cls.sub_url = json.loads(response.content)['url']

        # create a post to comment on.
        cls.post = Post.objects.create(
            title = 'A new Post',
            author = cls.account,
            body_text = 'Some post text',
            posted_in = cls.sub
        )

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

        for u in Notification.objects.all():
            print u.message
            print u.type
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.all()[0].message, "cameron mentioned you in a comment in Some New Sub")
        self.assertEqual(Notification.objects.all()[1].message, "cameron commented on your post in Some New Sub")
