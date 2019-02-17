from reddit_clone_django_rest.app.models import Sub, Post, Comment, User, Account
from faker import Faker
from random import randint

fake = Faker()

class FakeData(object):

    def create_fake_data(self, num_users, num_subs, num_posts_per_sub, should_create_comments):
        self.num_users=num_users

        for i in range(num_users):

            user = User.objects.create(
                username = fake.name() + str(i),
                password = '123d32' + str(i)
            )

            #print "Created user: " + user.username
    
        for i in range(num_subs):
            user_account = Account.objects.get(pk=randint(1, num_users))
            sub = Sub.objects.create(
                title = fake.sentence(),
                created_by = user_account
            )

            #print "Created sub: " + sub.title

            for i in range(num_posts_per_sub):
                post = Post.objects.create(
                    title = fake.sentence(),
                    author = user_account,
                    body_text = fake.text(),
                    posted_in = sub
                )

                #print "Created post: " + post.title + " in sub: " + sub.title

                # create top-level comments
                num_top_level_comments = randint(5, 20)
                for i in range(num_top_level_comments):
                    parent_comment = Comment.objects.create(
                        body_text=fake.sentence(),
                        author=Account.objects.get(pk=randint(1, num_users)),
                        post=post
                    )

                    #print "(" + str(i) + "/" + str(num_top_level_comments) + ")"  " created top-level comment " + str(parent_comment.id) + " for post: " + post.title

                    depth = randint(1, 10)

                    if should_create_comments:
                        self.create_comments(depth, parent_comment, post)


    def create_comments(self, depth, parent_comment, post):
        if depth == 0:
            return
        for i in range(depth):
            comment = Comment.objects.create(
                body_text=fake.sentence(),
                author=Account.objects.get(pk=randint(1, self.num_users)),
                post=post,
                parent=parent_comment
            )

            print "(" + str(i) + "/" + str(depth) + ")" " created child comment " + str(comment.id) + ", child of " + str(parent_comment.id) + " for post " + str(post.id)
        self.create_comments(depth-1, comment, post)





