from __future__ import absolute_import, unicode_literals
from itertools import chain
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
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


@shared_task
def vote(direction, user_id, kwargs):
    from django.core.cache import cache
    from reddit_clone_django_rest.app.models import Vote, Account

    existing_vote = Vote.objects.filter(
        user_id=user_id, **kwargs
    )

    if existing_vote.exists():
        existing_vote = existing_vote[0]
        if direction == existing_vote.direction:
            existing_vote.direction = constants.NONE
        else:
            existing_vote.direction = direction
        vote = existing_vote

    else:
        account = Account.objects.get(pk=user_id)
        new_vote = Vote.objects.create(
            user=account,
            direction=direction,
            **kwargs
        )
        vote = new_vote

    vote.save()
    cache.set(vote.get_cache_key(), vote.direction)

@task
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
def update_scores():
    from reddit_clone_django_rest.app.models import Post

    posts = Post.objects.prefetch_related(
        'comments').order_by('scores_last_generated')[:1000]

    post_count = len(posts)
    comment_count = 0

    for post in posts:
        print "Updating post " + str(post.id)
        _update_object_scores.s(post)

        post_comments = post.comments.all()
        comment_count += len(post_comments)

        for comment in post_comments:
            _update_object_scores.s(comment)

    print 'Successfully updated {} posts and {} comments.'.format(
        str(post_count), str(comment_count))
