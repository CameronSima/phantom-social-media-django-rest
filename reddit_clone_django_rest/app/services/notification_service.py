import string
import re
from pprint import pprint
from reddit_clone_django_rest.app.models import Account, Sub, User, Post, Comment, Notification, NOTIFICATION_TYPES
import reddit_clone_django_rest.app.constants as constants

def create_post_notifications(post):
    post_author = User.objects.only('username').get(pk=post.author.id)
    notify_sub_admins(post, post_author.username)


def notify_sub_admins(post, post_author):
    sub = Sub.objects.prefetch_related('admins').get(pk=post.posted_in.id)
    if sub.send_new_post_notifications:
        for user in sub.admins.all():
            message = post_author + ' posted in ' + sub.title
            create_post_notification(user, message, post, constants.USER_POSTED_IN_SUB)

def create_post_notification(user, message, post, type):
    Notification.objects.create(
        user = user,
        message = message,
        post = post,
        type = type
    )

def create_comment_notifications(comment):
    post = Post.objects.select_related('posted_in').get(pk=comment.post.id)
    sub_title = post.posted_in.title
    comment_author = User.objects.only('username').get(pk=comment.author.id)

    notify_mentioned_users(comment, comment_author.username, sub_title)
    notify_op(comment, comment_author.username, sub_title)


def notify_mentioned_users(comment, comment_author_username, sub_title):
    if '@' in comment.body_text:
        mentioned_user_names = {name.strip("@") for name in comment.body_text.split() if name.startswith("@")}

        regex = re.compile('[%s]' % re.escape(string.punctuation))
        for user in mentioned_user_names:
            user = user.encode('ascii')
            user = regex.sub('', user)
            user_obj = User.objects.select_related('account').get(username=user)
            if user_obj:
                message = comment_author_username + " mentioned you in a comment in " + sub_title
                create_comment_notification(user_obj.account, message, comment, constants.MENTIONED_USER)


def notify_op(comment, comment_author_name, sub_title):

    # Only notify post author if it's a top-level comment. Otherwise, 
    # notify the author of the parent comment.
    if comment.parent:
        notify_parent_comment_author(comment, comment_author_name, sub_title)  
    else:
        notify_post_author(comment, comment_author_name, sub_title)
        

def notify_post_author(comment, comment_author_name, sub_title):
    message = comment_author_name + " commented on your post in " + sub_title
    post = Post.objects.select_related('author').get(pk=comment.post.id)
    create_comment_notification(post.author, message, comment, constants.POST_AUTHOR)

def notify_parent_comment_author(comment, comment_author_name, sub_title):
    message = comment_author_name + " replied to your comment in " + sub_title
    parent_comment = Comment.objects.select_related('author').get(pk=comment.parent.id)
    create_comment_notification(parent_comment.author, message, comment, constants.COMMENT_PARENT_AUTHOR)

def create_comment_notification(user, message, comment, type):
    Notification.objects.create(
        user = user,
        message = message,
        comment = comment,
        type = type
    )

 