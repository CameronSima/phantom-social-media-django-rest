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

class PostTests(APITestCase):

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
        url = reverse('sub-detail', kwargs={'slug': cls.sub.slug})
        response = client.get(url, format='json')
        cls.sub_url = response.json()['url']


    def test_create_post(self):
        """
        Ensure we can create a new Post object.
        """

        url = reverse('post-list')
    
        data = { 'title': 'A test post', 'body_text': 'some text', 'posted_in': self.sub.id}
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.post(url, data, format='json')

        print "RESPONSE $$$$$$$$$$$$$$$$$$$$$$$$$"
        print response

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.get().title, 'A test post')


    def test_create_post_with_no_user_should_fail(self):
        """
        Ensure that trying to post without credentials
        fails and gives a helpful message.
        """

        url = reverse('post-list')
        data = { 'title': 'A test post', 'body_text': 'some text', 'body_html': 'some html', 'posted_in': self.sub_url}
        client = APIClient()
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 0)

        resData = json.loads(response.content)
        self.assertEqual(resData['detail'], 'Authentication credentials were not provided.')

    def test_can_upvote(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )
        url = reverse('post-upvote', kwargs={'slug': Post.objects.get().slug})
        #url = '/posts/?pk=' + str(Post.objects.get().id) + '/'
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(Post.objects.get().upvoted_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().upvoted_by.count(), 1)

    def test_can_downvote(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )
        url = reverse('post-downvote', kwargs={'slug': Post.objects.get().slug})
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(Post.objects.get().downvoted_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().downvoted_by.count(), 1)

    def test_user_cant_vote_twice(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )
        url = reverse('post-downvote', kwargs={'slug': Post.objects.get().slug})
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        # attempt to vote twice
        response = client.get(url, format='json')
        response = client.get(url, format='json')

       # self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.get().downvoted_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().downvoted_by.count(), 1)

    def test_user_can_comment_on_post(self):
        client = APIClient()
        post = Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )

        response = client.get('/posts/?pk=' + str(post.id) + '/')
        post_id = json.loads(response.content)['results'][0]['id']
    
        data = { 'title': 'A test post', 'parent': None, 'body_text': 'some text',  'post': post_id}
        url = reverse('comment-list')
        
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        response = client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get().post, post)
        
    def test_create_post_with_no_body_should_fail(self):
        """
        Ensure we can't submit a Post with no text'.
        """

        url = reverse('post-list')

        data = { 'title': 'A test post', 'posted_in': self.sub.id}
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_with_link_creates_preview_image(self):
        url = reverse('post-list')
        data = { 'title': 'A test post', 'link_url': 'https://pypi.org/project/webpreview/', 'body_text': 'some text', 'posted_in': self.sub.id}
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.get().title, 'A test post')

    def test_can_save_post(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )
        url = reverse('post-save', kwargs={'slug': Post.objects.get().slug})
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(Post.objects.get().saved_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().saved_by.count(), 1)

    def test_can_unsave_post(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )

        # Must save() first before unsaving, else will get and error in response.
        url = reverse('post-save', kwargs={'slug': Post.objects.get().slug})
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        client.get(url, format='json')

        url = reverse('post-unsave', kwargs={'slug': Post.objects.get().slug})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(not Post.objects.get().saved_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().saved_by.count(), 0)

    def test_user_cant_save_twice(self):
        Post.objects.create(
            author=self.account,
            title="Some post",
            body_text="some text",
            body_html="Some html",
            posted_in=self.sub
        )
        url = reverse('post-save', kwargs={'slug': Post.objects.get().slug})
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        response = client.get(url, format='json')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.get().saved_by.filter(pk=self.account.id).exists())
        self.assertEqual(Post.objects.get().saved_by.count(), 1)