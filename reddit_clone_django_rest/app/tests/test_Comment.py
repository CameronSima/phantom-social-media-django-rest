# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from reddit_clone_django_rest.app.models import User, Post, Sub, Account, Comment
from reddit_clone_django_rest.app.serializers import SubSerializer, PostSerializer

class CommentTests(APITestCase):
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

        # these are only added automatically when created via the api
        cls.sub.admins=[cls.account]
        cls.sub.subscribers=[cls.account]
        cls.sub.save()

        url = reverse('sub-detail', kwargs={'slug': cls.sub.slug})
        response = client.get(url, format='json')
        cls.sub_url = response.json()['url']

        # create a post to comment on.
        cls.post = Post.objects.create(
            title = 'A new Post',
            author = cls.account,
            body_text = 'Some post text',
            posted_in = cls.sub
        )

    def test_comment_can_be_deleted(self):

        comment = Comment.objects.create(
            body_text = 'this is a stupid thing to say!!',
            author=self.account,
            post=self.post
        )

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = reverse('post-detail', kwargs={'slug': self.post.slug})

        # now we see it...
        response = client.get(url, format='json')
        comments = response.json()['comments']
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['body_text'], 'this is a stupid thing to say!!')
        self.assertTrue(Comment.objects.get().is_visible)

        # delete the comment
        url = reverse('comment-delete', kwargs={'pk': comment.id})
        delete_response = client.patch(url, format='json')

        # ...now we don't
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        response = client.get(url, format='json')
        comments = response.json()['comments']

        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['body_text'], '- deleted -')
        self.assertEqual(delete_response.status_code, 202)
        self.assertFalse(Comment.objects.get().is_visible)

        
