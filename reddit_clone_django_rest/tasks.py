from __future__ import absolute_import, unicode_literals
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from celery import task, shared_task, Celery
import os
from celery.schedules import crontab
from reddit_clone_django_rest.app import constants
from .celery import app as celery_app


@shared_task
def upvote(**params):
    from reddit_clone_django_rest.app.services import vote_service

    vote_service.create_default_vote(**params)

def _update_object_scores(instance):
    from reddit_clone_django_rest.app.services import homepage_service

    ups = instance.votes.filter(direction=constants.UP).count()
    downs = instance.votes.filter(direction=constants.DOWN).count()

    instance.hot = homepage_service.hot(ups, downs, instance.created)
    instance.confidence = homepage_service.best(ups, downs)
    instance.score = homepage_service.score(ups, downs)
    instance.controversy = homepage_service.controversy(ups, downs)
    instance.scores_last_generated = datetime.now(tz=timezone.utc)
    instance.save()


@task
# @transaction.atomic
def update_scores():
    from reddit_clone_django_rest.app.models import Post

    posts = Post.objects.prefetch_related(
        'comments').order_by('scores_last_generated')[:10]

    post_count = len(posts)
    comment_count = 0


    for post in posts:
        print "Updating post " + str(post.id)
        _update_object_scores(post)

        post_comments = post.comments.all()
        comment_count += len(post_comments)

        for comment in post_comments:
            _update_object_scores(comment)

    print "Successfully updated " + str(post_count) + " posts and " + str(comment_count) + " comments."
