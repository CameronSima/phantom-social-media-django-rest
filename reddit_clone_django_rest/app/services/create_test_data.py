from reddit_clone_django_rest.app.models import User, Account, Post, Sub, Comment
from random import randint

class TestDataCreator:
    num_users = 2000
    num_posts = 100
    num_subs = 500
    num_comments = 500

    def run(self):
        # self.create_users()
        #self.create_subs()
        self.create_posts()

    def create_users(self):
        print "Creating users..."
        for i in range (0, self.num_users):
            User.objects.create_user(
                username="User " + str(i),
                password="password"
            )
    
    def create_subs(self):
        print "Creating Subs..."
        for i in range(0, self.num_subs):  
            account = Account.objects.get(id=randint(0, self.num_users))
            Sub.objects.create(
                title="A Sub " + str(i),
                created_by=account
            )

    def create_posts(self):
        print "Createing posts..."
        for i in range(0, self.num_posts):
            account = Account.objects.get(id=randint(0, self.num_users))
            sub = Sub.objects.get(id=randint(0, self.num_subs))
            Post.objects.create(
                title="a Post " + str(i),
                body_text="some text",
                body_html='<div>some text</div>',
                posted_in=sub,
                author=account
            )
