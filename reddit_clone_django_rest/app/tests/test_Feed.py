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
from reddit_clone_django_rest.app.scripts import create_fake_data
from reddit_clone_django_rest.app.services.homepage_service import hot

# Helpers
def all_posts_in_set_are_sorted_by_hot(posts):

    #ensure posts are sorted by hot
    all_posts_in_set_are_sorted = True
    for i in xrange(len(posts)-1):
        if posts[i]['hot'] < posts[i+1]['hot']:
            all_posts_in_set_are_sorted = False
    return all_posts_in_set_are_sorted

def all_posts_in_set_are_sorted_by_best(posts):

    #ensure posts are sorted by best
    all_posts_in_set_are_sorted = True
    for i in xrange(len(posts)-1):
        if posts[i]['best_ranking'] < posts[i+1]['best_ranking']:
            all_posts_in_set_are_sorted = False
    return all_posts_in_set_are_sorted

def all_posts_in_set_are_sorted_by_new(posts):

    #ensure posts are sorted by new
    all_posts_in_set_are_sorted = True
    for i in xrange(len(posts)-1):
        if posts[i]['created'] < posts[i+1]['created']:
            all_posts_in_set_are_sorted = False
    return all_posts_in_set_are_sorted

def user_is_subbed_to_all_posts(posts, account):

    # ensure the user is subbed to all subs the posts are posted in
    user_is_subbed_to_all = True
    for post in posts:
        post_obj = Post.objects.select_related('posted_in').get(pk=post['id'])
        sub = Sub.objects.get(pk=post_obj.posted_in.id)
        if account not in sub.subscribers.all():
            user_is_subbed_to_all = False
    return user_is_subbed_to_all



class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):

        print "### NOTE: IF ANY TESTS FAIL HERE, ENSURE HOTNESS IS RETURNED FROM THE SERIALIZER"
        client = APIClient()

        # create User
        cls.user = User.objects.create_user(
            username="cameron",
            password="123456"
        )

        #get token for requests
        cls.token = Token.objects.get(user__username="cameron").key

        # Get user's Account object
        cls.account = Account.objects.get(id=cls.user.id)
        response = client.get('/accounts/' + str(cls.account.id) + '/')
        cls.account_url = json.loads(response.content)['url']

    def test_create_fake_data(self):
        num_users = 1
        num_subs = 5
        num_posts_per_sub = 10
        create_fake_data(1, num_subs, num_posts_per_sub)

        self.assertEqual(Sub.objects.all().count(), num_subs)
        self.assertEqual(Account.objects.all().count(), num_users + 1)
        self.assertEqual(Post.objects.all().count(), num_posts_per_sub * num_subs)

    def test_front_page_is_sorted_by_hot(self):
        create_fake_data(1, 10, 15)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/home?sort=hot'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts3))

        # assert that the three result sets are sorted relative to one another
        all_results = posts1 + posts2 + posts3
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(all_results))

    def test_front_page_sorted_by_new(self):
        # cameron = Account.objects.get(user__username='cameron')
        create_fake_data(1, 10, 15)

        # for sub in Sub.objects.all():
        #     sub.subscribers.add(cameron)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/home?sort=new'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts3))

        # assert that the three result sets are sorted relative to one another
        all_results = posts1 + posts2 + posts3
        self.assertTrue(all_posts_in_set_are_sorted_by_new(all_results))

    def test_front_page_includes_no_private_posts(self):
        create_fake_data(1, 10, 15)

        #make some posts private
        posts = Post.objects.all()
        for post in posts:
            if post.id % 2 == 0:
                post.is_private = True
                post.save()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/home?sort=hot'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_hot(posts3))

        
        all_results = posts1 + posts2 + posts3
        all_posts_are_private = True
        for post in all_results:
            post_obj = Post.objects.select_related('posted_in').get(pk=post['id'])
            if post_obj.is_private:
                all_posts_are_private = False

            self.assertTrue(all_posts_are_private)


    def test_front_page_sorted_by_new(self):
        create_fake_data(1, 10, 15)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/home?sort=new'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts3))

        # assert that the three result sets are sorted relative to one another
        all_results = posts1 + posts2 + posts3

    def test_front_page_sorted_by_best(self):
        create_fake_data(1, 10, 15)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/home?sort=best'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_best(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_best(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_best(posts3))

        # assert that the three result sets are sorted relative to one another
        all_results = posts1 + posts2 + posts3
        self.assertTrue(all_posts_in_set_are_sorted_by_best(all_results))
        

    def test_user_subbed_posts_are_sorted(self):
        cameron = Account.objects.get(user__username='cameron')
        create_fake_data(1, 10, 15)

        for sub in Sub.objects.all():
            sub.subscribers.add(cameron)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/subbed_posts?sort=new'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']
        
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts1))

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts2))

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']
        self.assertTrue(all_posts_in_set_are_sorted_by_new(posts3))

        # assert that the three result sets are sorted relative to one another
        all_results = posts1 + posts2 + posts3
        self.assertTrue(all_posts_in_set_are_sorted_by_new(all_results))

    def test_user_subbed_posts_are_correct(self):
        cameron = Account.objects.get(user__username='cameron')
        create_fake_data(1, 10, 15)

        for sub in Sub.objects.all():
            sub.subscribers.add(cameron)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        url = '/subbed_posts?sort=new'
        response = client.get(url, format='json')
        next_url = response.json()['next']
        posts1 = response.json()['results']

        # get next result set
        response = client.get(next_url, format='json')
        posts2 = response.json()['results']
        next_url = response.json()['next']

        response = client.get(next_url, format='json')
        posts3 = response.json()['results']

        all_results = posts1 + posts2 + posts3
        
        # ensure the user is subbed to all subs the posts are posted in
        self.assertTrue(user_is_subbed_to_all_posts(all_results, cameron))








        


    


