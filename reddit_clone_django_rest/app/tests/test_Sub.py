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
from reddit_clone_django_rest.app.views import SubViewSet

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

        # # create Sub to post in, and fetch from api to get url property
        # cls.sub = Sub.objects.create(title="Some New Sub", created_by=cls.account)
        # response = client.get('/subs/' + str(cls.sub.id) + '/')
        # cls.sub_url = json.loads(response.content)['url']

    def test_create_sub(self):
        url = reverse('sub-list')
        data = { 'title': 'A New and Awesome Sub'}
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = client.post(url, data, format='json')

        self.assertEqual(Sub.objects.count(), 1)
        self.assertEqual(Sub.objects.get().created_by, self.account)
        self.assertTrue(self.account in Sub.objects.get().admins.all())
    
    def test_user_can_subscribe(self):
        Sub.objects.create(title="Some New Sub", created_by=self.account)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('sub-subscribe', kwargs={'slug': Sub.objects.get().slug})

        response = client.patch(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Sub.objects.prefetch_related('subscribers').get().subscribers.count(), 1)
        self.assertEqual(Account.objects.prefetch_related('subbed_to').get().subbed_to.all().get().title, 'Some New Sub')


    def test_user_can_unsubscribe(self):
        Sub.objects.create(title="Some New Sub", created_by=self.account)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        # first subscribe, then unsubscribe
        url = reverse('sub-subscribe', kwargs={'slug': Sub.objects.get().slug})
        response = client.patch(url, format='json')

        url = reverse('sub-unsubscribe', kwargs={'slug': Sub.objects.get().slug})
        response = client.patch(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Sub.objects.prefetch_related('subscribers').get().subscribers.count(), 0)
        self.assertEqual(Account.objects.prefetch_related('subbed_to').get().subbed_to.count(), 0)


    
