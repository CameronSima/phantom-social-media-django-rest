# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from rest_framework.test import APITestCase

# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from reddit_clone_django_rest.app.models import User

class UserTests(APITestCase):
    def test_create_account(self):
        """
        Ensure we can create a new User object.
        """
        url = reverse('user-list')
        data = {'username': 'cameron', 'password': '123456'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'cameron')

        # Ensure the password was encrypted.
        self.assertNotEqual(User.objects.get().password, '123456')

