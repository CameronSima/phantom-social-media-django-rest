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

class TestAccount(APITestCase):

    def test_can_signup(self):

        data = {'username': 'cameron', 'password': '2f2f235t2'}
        url = reverse('user-list')
        client = APIClient()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'cameron')
        self.assertEqual(Account.objects.get().user.username, 'cameron')